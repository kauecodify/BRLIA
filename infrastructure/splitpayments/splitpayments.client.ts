import { Injectable, OnModuleInit, Logger } from '@nestjs/common';
import { ClientGrpc, Client } from '@nestjs/microservices';
import { lastValueFrom, catchError, throwError } from 'rxjs';
import { Transport } from '@nestjs/microservices/enums';
import { join } from 'path';
import { MetricsService } from '../monitoring/metrics.service';
import { IdempotencyService } from '../idempotency/idempotency.service';

// ============================================================================
// Type Definitions
// ============================================================================

// Currency types
export type Currency = 'BRL' | 'USD' | 'EUR';

// Account types
export type AccountType = 'ESCROW' | 'BANK' | 'WALLET' | 'PIX' | 'CRYPTO';

// Split status
export type SplitStatus = 
    | 'PENDING'
    | 'PROCESSING'
    | 'TAX_CONSULTED'
    | 'SPLIT_CALCULATED'
    | 'GATEWAY_SUBMITTED'
    | 'GATEWAY_PROCESSING'
    | 'COMPLETED'
    | 'FAILED'
    | 'ESCROW_RETAINED'
    | 'CANCELLED'
    | 'REVERSED';

// Payment method
export type PaymentMethod = 
    | 'PIX'
    | 'BOLETO'
    | 'TED'
    | 'DOC'
    | 'CREDIT_CARD'
    | 'DEBIT_CARD';

// Bank account interface
export interface BankAccount {
    bankCode: string;
    agency: string;
    accountNumber: string;
    accountDigit?: string;
    documentNumber: string;
    documentType: string;
    holderName: string;
}

// PIX account interface
export interface PIXAccount {
    keyType: string;
    keyValue: string;
    holderName: string;
    documentNumber: string;
}

// Destination account interface
export interface DestinationAccount {
    accountType: AccountType;
    bankAccount?: BankAccount;
    pixAccount?: PIXAccount;
    externalId: string;
    metadata?: Record<string, string>;
}

// Split rule interface
export interface SplitRule {
    description: string;
    percentage: number;
    destination: DestinationAccount;
    metadata?: Record<string, string>;
}

// Tax information interface
export interface TaxInfo {
    cbsRate: number;
    cbsAmount: number;
    cbsAccountId: string;
    ibsRate: number;
    ibsAmount: number;
    ibsAccountId: string;
    totalTaxRate: number;
    totalTaxAmount: number;
}

// Gateway information interface
export interface GatewayInfo {
    gateway: string;
    transactionId: string;
    status: string;
    metadata?: Record<string, string>;
}

// Escrow information interface
export interface EscrowInfo {
    escrowAccountId: string;
    amountMinor: number;
    reason: string;
    retryInSeconds: number;
    metadata?: Record<string, string>;
}

// Error information interface
export interface ErrorInfo {
    code: string;
    message: string;
    details?: Record<string, string>;
}

// Split amounts interface
export interface SplitAmounts {
    supplier: DestinationAccount;
    supplierAmount: number;
    platformFee: DestinationAccount;
    platformFeeAmount: number;
    buyerReserve: DestinationAccount;
    buyerReserveAmount: number;
    lenderCost: DestinationAccount;
    lenderCostAmount: number;
}

// ============================================================================
// Request Types
// ============================================================================

// Request to create a split transaction
export interface CreateSplitRequest {
    idempotencyKey: string;
    transactionId: string;
    poolId: string;
    amountMinor: number;
    currency: Currency;
    referenceId?: string;
    supplierAccount: DestinationAccount;
    platformFeeAccount: DestinationAccount;
    buyerReserveAccount: DestinationAccount;
    lenderCostAccount: DestinationAccount;
    splitRules?: SplitRule[];
    taxInfo?: TaxInfo;
    metadata?: Record<string, string>;
}

// Request to get split status
export interface GetSplitStatusRequest {
    splitId: string;
    transactionId?: string;
}

// Request to list splits by transaction
export interface ListSplitsRequest {
    transactionId: string;
    poolId?: string;
    status?: SplitStatus;
    limit?: number;
    pageToken?: string;
}

// Request to cancel a split
export interface CancelSplitRequest {
    splitId: string;
    reason?: string;
    metadata?: Record<string, string>;
}

// ============================================================================
// Response Types
// ============================================================================

// Response for create split
export interface CreateSplitResponse {
    splitId: string;
    transactionId: string;
    status: SplitStatus;
    splitHash: string;
    processedAt: number; // nanoseconds
    splitAmounts: SplitAmounts;
    taxInfo?: TaxInfo;
    gatewayInfo?: GatewayInfo;
    escrowInfo?: EscrowInfo;
    errorInfo?: ErrorInfo;
    metadata?: Record<string, string>;
}

// Response for get split status
export interface GetSplitStatusResponse {
    splitId: string;
    transactionId: string;
    status: SplitStatus;
    amountMinor: number;
    currency: Currency;
    splitAmounts?: SplitAmounts;
    taxInfo?: TaxInfo;
    gatewayInfo?: GatewayInfo;
    escrowInfo?: EscrowInfo;
    errorInfo?: ErrorInfo;
    createdAt: number; // nanoseconds
    updatedAt: number; // nanoseconds
    metadata?: Record<string, string>;
}

// Response for list splits
export interface ListSplitsResponse {
    splits: GetSplitStatusResponse[];
    nextPageToken?: string;
    totalCount: number;
}

// Response for cancel split
export interface CancelSplitResponse {
    splitId: string;
    transactionId: string;
    status: SplitStatus;
    cancelledAt: number; // nanoseconds
    reason?: string;
    metadata?: Record<string, string>;
}

// ============================================================================
// gRPC Service Interface
// ============================================================================

interface SplitPaymentsService {
    createSplit: (request: CreateSplitRequest) => any;
    getSplitStatus: (request: GetSplitStatusRequest) => any;
    listSplitsByTransaction: (request: ListSplitsRequest) => any;
    cancelSplit: (request: CancelSplitRequest) => any;
}

// ============================================================================
// Client Implementation
// ============================================================================

@Injectable()
export class SplitPaymentsClient implements OnModuleInit {
    private readonly logger = new Logger(SplitPaymentsClient.name);
    
    @Client({
        transport: Transport.GRPC,
        options: {
            url: process.env.SPLITPAYMENTS_GRPC_URL || 'splitpayments.lowdataesc.gov.br:50053',
            package: 'brlia.splitpayments.v1',
            protoPath: join(__dirname, '../../../proto/splitpayments.proto'),
            loader: {
                keepCase: true,
            },
            tls: {
                cert: process.env.GRPC_CLIENT_CERT,
                key: process.env.GRPC_CLIENT_KEY,
                ca: process.env.GRPC_CA_CERT,
            },
        },
    })
    private client: ClientGrpc;
    
    private splitService: SplitPaymentsService;
    
    constructor(
        private readonly metrics: MetricsService,
        private readonly idempotency: IdempotencyService,
    ) {}
    
    async onModuleInit() {
        this.splitService = this.client.getService<SplitPaymentsService>('SplitPaymentsService');
        this.logger.log('SplitPaymentsClient initialized');
    }
    
    // ============================================================================
    // Main Methods
    // ============================================================================
    
    /**
     * Create a new split transaction
     */
    async createSplit(request: CreateSplitRequest): Promise<CreateSplitResponse> {
        const startTime = Date.now();
        const gateway = request.gatewayInfo?.gateway || 'unknown';
        
        try {
            // Generate idempotency key if not provided
            const idempotencyKey = request.idempotencyKey || 
                this.idempotency.generateKey('split', request);
            
            // Check idempotency
            const { isNew, existing } = await this.idempotency.checkAndSet(
                idempotencyKey,
                { request, timestamp: Date.now() }
            );
            
            if (!isNew && existing) {
                this.logger.log(`Duplicate split request detected (idempotency key: ${idempotencyKey})`);
                return existing as CreateSplitResponse;
            }
            
            // Execute gRPC call
            const response = await lastValueFrom(
                this.splitService.createSplit(request).pipe(
                    catchError((error) => {
                        this.logger.error(`gRPC call failed: ${error.message}`, error);
                        return throwError(() => error);
                    })
                )
            );
            
            const latencyMs = Date.now() - startTime;
            
            // Record metrics
            this.metrics.observeSplitLatency(
                gateway,
                response.status,
                latencyMs / 1000
            );
            
            if (response.status === 'COMPLETED' || response.status === 'PENDING') {
                this.metrics.incrementSplitSuccess(gateway);
            } else {
                this.metrics.incrementSplitFailure(
                    gateway,
                    response.errorInfo?.code || 'UNKNOWN'
                );
            }
            
            this.logger.debug(`Split created successfully`, {
                splitId: response.splitId,
                transactionId: response.transactionId,
                status: response.status,
                latencyMs,
            });
            
            return response;
        } catch (error) {
            const latencyMs = Date.now() - startTime;
            
            this.metrics.observeSplitLatency(gateway, 'FAILED', latencyMs / 1000);
            this.metrics.incrementSplitFailure(gateway, error.code || 'GRPC_ERROR');
            
            this.logger.error(`Failed to create split`, {
                error: error.message,
                request: {
                    transactionId: request.transactionId,
                    amountMinor: request.amountMinor,
                },
                latencyMs,
            });
            
            throw error;
        }
    }
    
    /**
     * Get the status of a split transaction
     */
    async getSplitStatus(request: GetSplitStatusRequest): Promise<GetSplitStatusResponse> {
        const startTime = Date.now();
        
        try {
            const response = await lastValueFrom(
                this.splitService.getSplitStatus(request).pipe(
                    catchError((error) => {
                        this.logger.error(`Failed to get split status: ${error.message}`, error);
                        return throwError(() => error);
                    })
                )
            );
            
            const latencyMs = Date.now() - startTime;
            this.metrics.observeSplitLatency(
                'unknown',
                response.status,
                latencyMs / 1000
            );
            
            return response;
        } catch (error) {
            this.logger.error(`Failed to get split status`, {
                error: error.message,
                splitId: request.splitId,
            });
            throw error;
        }
    }
    
    /**
     * List splits by transaction
     */
    async listSplits(request: ListSplitsRequest): Promise<ListSplitsResponse> {
        try {
            const response = await lastValueFrom(
                this.splitService.listSplitsByTransaction(request)
            );
            return response;
        } catch (error) {
            this.logger.error(`Failed to list splits`, {
                error: error.message,
                transactionId: request.transactionId,
            });
            throw error;
        }
    }
    
    /**
     * Cancel a split transaction
     */
    async cancelSplit(request: CancelSplitRequest): Promise<CancelSplitResponse> {
        try {
            const response = await lastValueFrom(
                this.splitService.cancelSplit(request)
            );
            return response;
        } catch (error) {
            this.logger.error(`Failed to cancel split`, {
                error: error.message,
                splitId: request.splitId,
            });
            throw error;
        }
    }
    
    // ============================================================================
    // Helper Methods
    // ============================================================================
    
    /**
     * Create a split with default rules
     */
    async createSplitWithDefaults(
        transactionId: string,
        poolId: string,
        amountMinor: number,
        currency: Currency,
        supplierAccount: DestinationAccount,
        referenceId?: string,
        metadata?: Record<string, string>,
    ): Promise<CreateSplitResponse> {
        // Default accounts (can be configured)
        const platformFeeAccount: DestinationAccount = {
            accountType: 'BANK',
            externalId: 'BRLIA_MAIN_ESCROW',
            bankAccount: {
                bankCode: '104',
                agency: '0001',
                accountNumber: '12345678',
                documentNumber: '00000000000100',
                documentType: 'CNPJ',
                holderName: 'BRLIA OPERACOES FINANCEIRAS',
            },
        };
        
        const buyerReserveAccount: DestinationAccount = {
            accountType: 'ESCROW',
            externalId: 'BUYER_RESERVE_POOL',
        };
        
        const lenderCostAccount: DestinationAccount = {
            accountType: 'BANK',
            externalId: 'LENDER_COST_ACCOUNT',
            bankAccount: {
                bankCode: '001',
                agency: '0001',
                accountNumber: '99999999',
                documentNumber: '00000000000101',
                documentType: 'CNPJ',
                holderName: 'LENDER BANK S.A.',
            },
        };
        
        const request: CreateSplitRequest = {
            idempotencyKey: this.idempotency.generateKey('split', {
                transactionId,
                amountMinor,
            }),
            transactionId,
            poolId,
            amountMinor,
            currency,
            referenceId,
            supplierAccount,
            platformFeeAccount,
            buyerReserveAccount,
            lenderCostAccount,
            splitRules: [
                {
                    description: 'Taxa da plataforma BRLIA',
                    percentage: 0.01,
                    destination: platformFeeAccount,
                },
                {
                    description: 'Reserva do comprador',
                    percentage: 0.02,
                    destination: buyerReserveAccount,
                },
                {
                    description: 'Custo do capital (Lender)',
                    percentage: 0.03,
                    destination: lenderCostAccount,
                },
                {
                    description: 'Valor líquido ao fornecedor',
                    percentage: 0.94,
                    destination: supplierAccount,
                },
            ],
            metadata,
        };
        
        return this.createSplit(request);
    }
    
    /**
     * Get split status by transaction ID
     */
    async getSplitStatusByTransaction(transactionId: string): Promise<GetSplitStatusResponse | null> {
        try {
            const response = await this.getSplitStatus({ transactionId });
            return response;
        } catch (error) {
            if (error.code === 'NOT_FOUND') {
                return null;
            }
            throw error;
        }
    }
    
    /**
     * Check if split is completed
     */
    async isSplitCompleted(splitId: string): Promise<boolean> {
        const status = await this.getSplitStatus({ splitId });
        return status.status === 'COMPLETED';
    }
    
    /**
     * Check if split is in escrow
     */
    async isSplitInEscrow(splitId: string): Promise<boolean> {
        const status = await this.getSplitStatus({ splitId });
        return status.status === 'ESCROW_RETAINED';
    }
}
