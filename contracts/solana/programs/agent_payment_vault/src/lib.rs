use anchor_lang::prelude::*;
use anchor_spl::token::{self, Mint, Token, TokenAccount, Transfer};

declare_id!("x402VauLt1111111111111111111111111111111111");

/// AgentPaymentVault: Solana Anchor Program for Autonomous AI Agent x402 Micropayments
/// 1:1 Solana native implementation of contracts/AgentPaymentVault.sol
#[program]
pub mod agent_payment_vault {
    use super::*;

    /// 1. Initialize the global vault and treasury config
    pub fn initialize(
        ctx: Context<Initialize>,
        treasury_wallet: Pubkey,
    ) -> Result<()> {
        let vault_config = &mut ctx.accounts.vault_config;
        vault_config.authority = ctx.accounts.authority.key();
        vault_config.treasury_wallet = treasury_wallet;
        vault_config.usdc_mint = ctx.accounts.usdc_mint.key();
        vault_config.vault_token_account = ctx.accounts.vault_token_account.key();
        vault_config.bump = ctx.bumps.vault_config;
        vault_config.vault_bump = ctx.bumps.vault_token_account;
        vault_config.total_settled_usdc = 0;

        emit!(VaultInitialized {
            authority: vault_config.authority,
            treasury_wallet,
            usdc_mint: vault_config.usdc_mint,
            vault_token_account: vault_config.vault_token_account,
        });

        Ok(())
    }

    /// 2. Agent pre-funds their on-chain vault with Native SPL USDC
    /// Equivalent to `deposit(uint256 amount)` in AgentPaymentVault.sol
    pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
        require!(amount > 0, VaultError::ZeroDepositAmount);

        // Transfer SPL USDC from agent's token account to the vault PDA token account
        let cpi_accounts = Transfer {
            from: ctx.accounts.agent_token_account.to_account_info(),
            to: ctx.accounts.vault_token_account.to_account_info(),
            authority: ctx.accounts.agent.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);
        token::transfer(cpi_ctx, amount)?;

        // Update Agent Vault Record
        let agent_record = &mut ctx.accounts.agent_record;
        if agent_record.agent == Pubkey::default() {
            agent_record.agent = ctx.accounts.agent.key();
            agent_record.created_at = Clock::get()?.unix_timestamp;
        }

        agent_record.balance = agent_record
            .balance
            .checked_add(amount)
            .ok_or(VaultError::MathOverflow)?;
        agent_record.total_deposited = agent_record
            .total_deposited
            .checked_add(amount)
            .ok_or(VaultError::MathOverflow)?;
        agent_record.last_updated_at = Clock::get()?.unix_timestamp;

        emit!(Deposited {
            agent: ctx.accounts.agent.key(),
            amount,
            new_balance: agent_record.balance,
        });

        Ok(())
    }

    /// 3. Settle agent spent amount to Treasury Wallet (Authority only)
    /// Equivalent to `settleAgentBatch` in AgentPaymentVault.sol
    pub fn settle_agent(
        ctx: Context<SettleAgent>,
        amount: u64,
    ) -> Result<()> {
        require!(amount > 0, VaultError::ZeroSettleAmount);

        let agent_record = &mut ctx.accounts.agent_record;
        require!(
            agent_record.balance >= amount,
            VaultError::InsufficientAgentBalance
        );

        // Deduct from agent on-chain vault record
        agent_record.balance = agent_record
            .balance
            .checked_sub(amount)
            .ok_or(VaultError::MathUnderflow)?;
        agent_record.total_spent = agent_record
            .total_spent
            .checked_add(amount)
            .ok_or(VaultError::MathOverflow)?;
        agent_record.last_updated_at = Clock::get()?.unix_timestamp;

        // Transfer SPL USDC from vault PDA to treasury wallet
        let usdc_mint_key = ctx.accounts.vault_config.usdc_mint;
        let bump = ctx.accounts.vault_config.bump;
        let signer_seeds: &[&[&[u8]]] = &[&[
            b"vault_config".as_ref(),
            usdc_mint_key.as_ref(),
            &[bump],
        ]];

        let cpi_accounts = Transfer {
            from: ctx.accounts.vault_token_account.to_account_info(),
            to: ctx.accounts.treasury_token_account.to_account_info(),
            authority: ctx.accounts.vault_config.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new_with_signer(cpi_program, cpi_accounts, signer_seeds);
        token::transfer(cpi_ctx, amount)?;

        // Record global metrics
        let vault_config = &mut ctx.accounts.vault_config;
        vault_config.total_settled_usdc = vault_config
            .total_settled_usdc
            .checked_add(amount)
            .ok_or(VaultError::MathOverflow)?;

        emit!(Settled {
            agent: agent_record.agent,
            amount,
            remaining_balance: agent_record.balance,
            treasury: vault_config.treasury_wallet,
        });

        Ok(())
    }

    /// 4. Update the treasury payout wallet (Authority only)
    pub fn update_treasury(
        ctx: Context<UpdateTreasury>,
        new_treasury_wallet: Pubkey,
    ) -> Result<()> {
        let vault_config = &mut ctx.accounts.vault_config;
        let old_treasury = vault_config.treasury_wallet;
        vault_config.treasury_wallet = new_treasury_wallet;

        emit!(TreasuryUpdated {
            previous_treasury: old_treasury,
            new_treasury: new_treasury_wallet,
        });

        Ok(())
    }
}

// =========================================================================
// Context Accounts
// =========================================================================

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + VaultConfig::INIT_SPACE,
        seeds = [b"vault_config", usdc_mint.key().as_ref()],
        bump
    )]
    pub vault_config: Account<'info, VaultConfig>,

    pub usdc_mint: Account<'info, Mint>,

    #[account(
        init,
        payer = authority,
        token::mint = usdc_mint,
        token::authority = vault_config,
        seeds = [b"vault_tokens", usdc_mint.key().as_ref()],
        bump
    )]
    pub vault_token_account: Account<'info, TokenAccount>,

    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
    pub rent: Sysvar<'info, Rent>,
}

#[derive(Accounts)]
pub struct Deposit<'info> {
    #[account(
        seeds = [b"vault_config", vault_config.usdc_mint.as_ref()],
        bump = vault_config.bump
    )]
    pub vault_config: Account<'info, VaultConfig>,

    #[account(
        mut,
        seeds = [b"vault_tokens", vault_config.usdc_mint.as_ref()],
        bump = vault_config.vault_bump
    )]
    pub vault_token_account: Account<'info, TokenAccount>,

    #[account(
        init_if_needed,
        payer = agent,
        space = 8 + AgentVaultRecord::INIT_SPACE,
        seeds = [b"agent_vault", agent.key().as_ref()],
        bump
    )]
    pub agent_record: Account<'info, AgentVaultRecord>,

    #[account(mut)]
    pub agent: Signer<'info>,

    #[account(
        mut,
        constraint = agent_token_account.mint == vault_config.usdc_mint,
        constraint = agent_token_account.owner == agent.key()
    )]
    pub agent_token_account: Account<'info, TokenAccount>,

    pub token_program: Program<'info, Token>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct SettleAgent<'info> {
    #[account(
        mut,
        has_one = authority @ VaultError::Unauthorized,
        seeds = [b"vault_config", vault_config.usdc_mint.as_ref()],
        bump = vault_config.bump
    )]
    pub vault_config: Account<'info, VaultConfig>,

    #[account(
        mut,
        seeds = [b"vault_tokens", vault_config.usdc_mint.as_ref()],
        bump = vault_config.vault_bump
    )]
    pub vault_token_account: Account<'info, TokenAccount>,

    #[account(
        mut,
        seeds = [b"agent_vault", agent_record.agent.as_ref()],
        bump
    )]
    pub agent_record: Account<'info, AgentVaultRecord>,

    #[account(
        mut,
        constraint = treasury_token_account.mint == vault_config.usdc_mint,
        constraint = treasury_token_account.owner == vault_config.treasury_wallet
    )]
    pub treasury_token_account: Account<'info, TokenAccount>,

    pub authority: Signer<'info>,
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct UpdateTreasury<'info> {
    #[account(
        mut,
        has_one = authority @ VaultError::Unauthorized,
        seeds = [b"vault_config", vault_config.usdc_mint.as_ref()],
        bump = vault_config.bump
    )]
    pub vault_config: Account<'info, VaultConfig>,

    pub authority: Signer<'info>,
}

// =========================================================================
// Data State Accounts
// =========================================================================

#[account]
#[derive(InitSpace)]
pub struct VaultConfig {
    pub authority: Pubkey,
    pub treasury_wallet: Pubkey,
    pub usdc_mint: Pubkey,
    pub vault_token_account: Pubkey,
    pub bump: u8,
    pub vault_bump: u8,
    pub total_settled_usdc: u64,
}

#[account]
#[derive(InitSpace)]
pub struct AgentVaultRecord {
    pub agent: Pubkey,
    pub balance: u64,
    pub total_deposited: u64,
    pub total_spent: u64,
    pub created_at: i64,
    pub last_updated_at: i64,
}

// =========================================================================
// Events
// =========================================================================

#[event]
pub struct VaultInitialized {
    pub authority: Pubkey,
    pub treasury_wallet: Pubkey,
    pub usdc_mint: Pubkey,
    pub vault_token_account: Pubkey,
}

#[event]
pub struct Deposited {
    pub agent: Pubkey,
    pub amount: u64,
    pub new_balance: u64,
}

#[event]
pub struct Settled {
    pub agent: Pubkey,
    pub amount: u64,
    pub remaining_balance: u64,
    pub treasury: Pubkey,
}

#[event]
pub struct TreasuryUpdated {
    pub previous_treasury: Pubkey,
    pub new_treasury: Pubkey,
}

// =========================================================================
// Custom Errors
// =========================================================================

#[error_code]
pub enum VaultError {
    #[msg("Deposit amount must be greater than zero.")]
    ZeroDepositAmount,
    #[msg("Settlement amount must be greater than zero.")]
    ZeroSettleAmount,
    #[msg("Agent vault record has insufficient balance.")]
    InsufficientAgentBalance,
    #[msg("Caller is not authorized to execute this action.")]
    Unauthorized,
    #[msg("Arithmetic overflow.")]
    MathOverflow,
    #[msg("Arithmetic underflow.")]
    MathUnderflow,
}
