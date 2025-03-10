import type * as types from './types';
import type { ConfigOptions, FetchResponse } from 'api/dist/core'
import Oas from 'oas';
import APICore from 'api/dist/core';
import definition from './openapi.json';

class SDK {
  spec: Oas;
  core: APICore;

  constructor() {
    this.spec = Oas.init(definition);
    this.core = new APICore(this.spec, 'bluefin-exchange/2.0.0 (api/6.1.3)');
  }

  /**
   * Optionally configure various options that the SDK allows.
   *
   * @param config Object of supported SDK options and toggles.
   * @param config.timeout Override the default `fetch` request timeout of 30 seconds. This number
   * should be represented in milliseconds.
   */
  config(config: ConfigOptions) {
    this.core.setConfig(config);
  }

  /**
   * If the API you're using requires authentication you can supply the required credentials
   * through this method and the library will magically determine how they should be used
   * within your API request.
   *
   * With the exception of OpenID and MutualTLS, it supports all forms of authentication
   * supported by the OpenAPI specification.
   *
   * @example <caption>HTTP Basic auth</caption>
   * sdk.auth('username', 'password');
   *
   * @example <caption>Bearer tokens (HTTP or OAuth 2)</caption>
   * sdk.auth('myBearerToken');
   *
   * @example <caption>API Keys</caption>
   * sdk.auth('myApiKey');
   *
   * @see {@link https://spec.openapis.org/oas/v3.0.3#fixed-fields-22}
   * @see {@link https://spec.openapis.org/oas/v3.1.0#fixed-fields-22}
   * @param values Your auth credentials for the API; can specify up to two strings or numbers.
   */
  auth(...values: string[] | number[]) {
    this.core.setAuth(...values);
    return this;
  }

  /**
   * If the API you're using offers alternate server URLs, and server variables, you can tell
   * the SDK which one to use with this method. To use it you can supply either one of the
   * server URLs that are contained within the OpenAPI definition (along with any server
   * variables), or you can pass it a fully qualified URL to use (that may or may not exist
   * within the OpenAPI definition).
   *
   * @example <caption>Server URL with server variables</caption>
   * sdk.server('https://{region}.api.example.com/{basePath}', {
   *   name: 'eu',
   *   basePath: 'v14',
   * });
   *
   * @example <caption>Fully qualified server URL</caption>
   * sdk.server('https://eu.api.example.com/v14');
   *
   * @param url Server URL
   * @param variables An object of variables to replace into the server URL.
   */
  server(url: string, variables = {}) {
    this.core.setServer(url, variables);
  }

  /**
   * Retrieves combined exchange info, market, and metadata.
   *
   */
  getMasterInfo(metadata?: types.GetMasterInfoMetadataParam): Promise<FetchResponse<200, types.GetMasterInfoResponse200>> {
    return this.core.fetch('/masterInfo', 'get', metadata);
  }

  /**
   * Retrieves candle stick data for a market.
   *
   */
  getCandlestickData(metadata: types.GetCandlestickDataMetadataParam): Promise<FetchResponse<200, types.GetCandlestickDataResponse200>> {
    return this.core.fetch('/candlestickData', 'get', metadata);
  }

  /**
   * Retrieves meta information of markets.
   *
   */
  getExchangeInfo(metadata?: types.GetExchangeInfoMetadataParam): Promise<FetchResponse<200, types.GetExchangeInfoResponse200>> {
    return this.core.fetch('/exchangeInfo', 'get', metadata);
  }

  /**
   * Retrieves markets information
   *
   */
  getMarketData(metadata?: types.GetMarketDataMetadataParam): Promise<FetchResponse<200, types.GetMarketDataResponse200>> {
    return this.core.fetch('/marketData', 'get', metadata);
  }

  /**
   * Retrieves markets available on the exchange.
   * This function does not take any input parameter
   *
   */
  getMarketSymbols(): Promise<FetchResponse<200, types.GetMarketSymbolsResponse200>> {
    return this.core.fetch('/marketData/symbols', 'get');
  }

  /**
   * Retrieves contract addresses of single or all markets available on the exchange
   *
   */
  getContractAddresses(metadata?: types.GetContractAddressesMetadataParam): Promise<FetchResponse<200, types.GetContractAddressesResponse200>> {
    return this.core.fetch('/marketData/contractAddresses', 'get', metadata);
  }

  /**
   * Retrieves the market contract addresses, chain rpc/URL, and other data.
   *
   */
  getMeta(metadata?: types.GetMetaMetadataParam): Promise<FetchResponse<200, types.GetMetaResponse200>> {
    return this.core.fetch('/meta', 'get', metadata);
  }

  /**
   * Allows user to get their orders on exchange
   *
   */
  getOrder(metadata?: types.GetOrderMetadataParam): Promise<FetchResponse<200, types.GetOrderResponse200>> {
    return this.core.fetch('/orders', 'get', metadata);
  }

  /**
   * Allows user to place a signed order on the exchange
   *
   */
  createOrder(body: types.CreateOrderBodyParam, metadata?: types.CreateOrderMetadataParam): Promise<FetchResponse<201, types.CreateOrderResponse201>> {
    return this.core.fetch('/orders', 'post', body, metadata);
  }

  /**
   * Allows user to get their open orders on the exchange
   *
   */
  getOpenOrder(metadata?: types.GetOpenOrderMetadataParam): Promise<FetchResponse<200, types.GetOpenOrderResponse200>> {
    return this.core.fetch('/orders/open-orders', 'get', metadata);
  }

  /**
   * Allows user to get their orders on the exchange
   *
   */
  getOrdersByOrderType(metadata?: types.GetOrdersByOrderTypeMetadataParam): Promise<FetchResponse<200, types.GetOrdersByOrderTypeResponse200>> {
    return this.core.fetch('/orders/by-order-type', 'get', metadata);
  }

  /**
   * Allows user to submit cancellation request for order(s) on the exchange
   * The cancellation signature must first be generated as a pre-requisite to this method
   *
   */
  deleteOrders(): Promise<FetchResponse<200, types.DeleteOrdersResponse200>> {
    return this.core.fetch('/orders/hash', 'delete');
  }

  /**
   * Retrieves state of orderbook
   *
   */
  getOrderbook(metadata: types.GetOrderbookMetadataParam): Promise<FetchResponse<200, types.GetOrderbookResponse200>> {
    return this.core.fetch('/orderbook', 'get', metadata);
  }

  /**
   * Retrieves recent trades executed on a market
   *
   */
  getRecentTrade(metadata: types.GetRecentTradeMetadataParam): Promise<FetchResponse<200, types.GetRecentTradeResponse200>> {
    return this.core.fetch('/recentTrades', 'get', metadata);
  }

  /**
   * Retrieves the status of exchange, if it's up or down
   *
   */
  getExchangeStatus(): Promise<FetchResponse<200, types.GetExchangeStatusResponse200>> {
    return this.core.fetch('/status', 'get');
  }

  getReferralDetails(): Promise<FetchResponse<200, types.GetReferralDetailsResponse200>> {
    return this.core.fetch('/tareferral/getReferralDetails', 'get');
  }

  linkAccount(body: types.LinkAccountBodyParam): Promise<FetchResponse<number, unknown>> {
    return this.core.fetch('/tareferral/linkAccount', 'put', body);
  }

  generateReferralLink(): Promise<FetchResponse<200, types.GenerateReferralLinkResponse200>> {
    return this.core.fetch('/tareferral/genReferral', 'put');
  }

  getPartnerDetails(): Promise<FetchResponse<200, types.GetPartnerDetailsResponse200>> {
    return this.core.fetch('/tareferral/getPartnerDetails', 'get');
  }

  getRefereeDetailsByPartner(metadata?: types.GetRefereeDetailsByPartnerMetadataParam): Promise<FetchResponse<200, types.GetRefereeDetailsByPartnerResponse200>> {
    return this.core.fetch('/tareferral/getRefereesByPartner', 'get', metadata);
  }

  getMemberDetails(): Promise<FetchResponse<200, types.GetMemberDetailsResponse200>> {
    return this.core.fetch('/tareferral/getMemberDetails', 'get');
  }

  getMembersMonthlyOverview(metadata?: types.GetMembersMonthlyOverviewMetadataParam): Promise<FetchResponse<200, types.GetMembersMonthlyOverviewResponse200>> {
    return this.core.fetch('/tareferral/getMembersMonthlyOverview', 'get', metadata);
  }

  /**
   * Retrieves user the history of transactions performed on the exchange
   *
   */
  getUserTransactionHistory(metadata?: types.GetUserTransactionHistoryMetadataParam): Promise<FetchResponse<200, types.GetUserTransactionHistoryResponse200>> {
    return this.core.fetch('/userTransactionHistory', 'get', metadata);
  }

  /**
   * Retrieves user current open position on the exchange
   *
   */
  getUserPosition(metadata?: types.GetUserPositionMetadataParam): Promise<FetchResponse<200, types.GetUserPositionResponse200>> {
    return this.core.fetch('/userPosition', 'get', metadata);
  }

  /**
   * Retrieves user's transfer history on exchange.
   *
   */
  getUserTransfer(metadata?: types.GetUserTransferMetadataParam): Promise<FetchResponse<200, types.GetUserTransferResponse200>> {
    return this.core.fetch('/userTransferHistory', 'get', metadata);
  }

  getAuxiliaryAddresses(): Promise<FetchResponse<200, types.GetAuxiliaryAddressesResponse200>> {
    return this.core.fetch('/config', 'get');
  }

  /**
   * Retrieves market funding rate data.
   *
   */
  getFundingRate(metadata: types.GetFundingRateMetadataParam): Promise<FetchResponse<200, types.GetFundingRateResponse200>> {
    return this.core.fetch('/fundingRate', 'get', metadata);
  }

  get(): Promise<FetchResponse<200, types.GetResponse200>> {
    return this.core.fetch('/', 'get');
  }

  /**
   * Retrieves the market price, price direction, price change, and other data.
   *
   */
  ticker(metadata?: types.TickerMetadataParam): Promise<FetchResponse<200, types.TickerResponse200>> {
    return this.core.fetch('/ticker', 'get', metadata);
  }

  /**
   * Retrieves user funding history on exchange.
   *
   */
  getUserFundingHistory(metadata?: types.GetUserFundingHistoryMetadataParam): Promise<FetchResponse<200, types.GetUserFundingHistoryResponse200>> {
    return this.core.fetch('/userFundingHistory', 'get', metadata);
  }

  /**
   * Generates a referral code for a specific campaign. New users can use this referral code
   * during registration, to associate themselves with the referring campaign and user.
   *
   */
  generateRefferalCode(body: types.GenerateRefferalCodeBodyParam): Promise<FetchResponse<200, types.GenerateRefferalCodeResponse200>> {
    return this.core.fetch('/growth/generateCode', 'post', body);
  }

  /**
   * Links a referred user to a specific campaign using a referral code.
   * This process associates the referred user's address with the campaign
   * and the user who referred them. Upon successful linking, the method
   * returns information about the referral, including the referral code and referee address.
   *
   */
  linkReferredUser(body: types.LinkReferredUserBodyParam): Promise<FetchResponse<200, types.LinkReferredUserResponse200>> {
    return this.core.fetch('/growth/linkReferredUser', 'post', body);
  }

  /**
   * Allows user to check the referrer info against any campaign Id
   *
   */
  getReferrerInfo(metadata: types.GetReferrerInfoMetadataParam): Promise<FetchResponse<200, types.GetReferrerInfoResponse200>> {
    return this.core.fetch('/growth/getReferrerInfo', 'get', metadata);
  }

  /**
   * Retrieves details about campaigns
   *
   */
  getCampaignDetails(): Promise<FetchResponse<200, types.GetCampaignDetailsResponse200>> {
    return this.core.fetch('/growth/campaignDetails', 'get');
  }

  /**
   * Retrieves reward details for a specific campaign based on the provided campaign Id
   * It returns information about the rewards associated with the campaign.
   *
   */
  getCampaignRewards(metadata: types.GetCampaignRewardsMetadataParam): Promise<FetchResponse<200, types.GetCampaignRewardsResponse200>> {
    return this.core.fetch('/growth/campaignRewards', 'get', metadata);
  }

  /**
   * Retrieves affiliate payout details for a specific campaign based on the provided
   * campaignId.
   *
   */
  getAffiliatePayouts(metadata: types.GetAffiliatePayoutsMetadataParam): Promise<FetchResponse<200, types.GetAffiliatePayoutsResponse200>> {
    return this.core.fetch('/growth/affiliate/payouts', 'get', metadata);
  }

  /**
   * Retrieves affiliate referee details based on the provided parameters.
   *
   */
  getRefereeDetails(metadata: types.GetRefereeDetailsMetadataParam): Promise<FetchResponse<200, types.GetRefereeDetailsResponse200>> {
    return this.core.fetch('/growth/affiliate/refereeDetails', 'get', metadata);
  }

  /**
   * Retrieves the count of affiliate referees for a specific campaign based on the provided
   * campaign Id
   *
   */
  getRefereesCount(metadata: types.GetRefereesCountMetadataParam): Promise<FetchResponse<200, types.GetRefereesCountResponse200>> {
    return this.core.fetch('/growth/affiliate/refereesCount', 'get', metadata);
  }

  /**
   * Retrieves the rewards history for a user, providing information
   * about the rewards they have earned from different programs
   *
   */
  getUserRewardsHistory(metadata?: types.GetUserRewardsHistoryMetadataParam): Promise<FetchResponse<200, types.GetUserRewardsHistoryResponse200>> {
    return this.core.fetch('/growth/userRewards/history', 'get', metadata);
  }

  /**
   * Retrieves a summary of the rewards earned by a user across different campaigns.
   *
   */
  getUserRewardsSummary(): Promise<FetchResponse<200, types.GetUserRewardsSummaryResponse200>> {
    return this.core.fetch('/growth/userRewards/summary', 'get');
  }

  /**
   * Retrieves an overview of trade and earns rewards for
   * a specific campaign based on the provided campaign Id
   *
   */
  getTradeAndEarnRewardsOverview(metadata: types.GetTradeAndEarnRewardsOverviewMetadataParam): Promise<FetchResponse<200, types.GetTradeAndEarnRewardsOverviewResponse200>> {
    return this.core.fetch('/growth/tradeAndEarn/rewardsOverview', 'get', metadata);
  }

  /**
   * Retrieves detailed information about trade and earns rewards
   * for a specific campaign based on the provided parameters
   *
   */
  getTradeAndEarnRewardsDetail(metadata: types.GetTradeAndEarnRewardsDetailMetadataParam): Promise<FetchResponse<200, types.GetTradeAndEarnRewardsDetailResponse200>> {
    return this.core.fetch('/growth/tradeAndEarn/rewardsDetail', 'get', metadata);
  }

  /**
   * Retrieves the total historical trading rewards earned by users
   *
   */
  totalHistoricalTradingRewards(): Promise<FetchResponse<200, types.TotalHistoricalTradingRewardsResponse200>> {
    return this.core.fetch('/growth/tradeAndEarn/totalHistoricalTradingRewards', 'get');
  }

  /**
   * Retrieves a summary of maker rewards, providing information about
   * historical rewards, active rewards, and pending rewards for market makers.
   *
   */
  getMakerRewardsSummary(): Promise<FetchResponse<200, types.GetMakerRewardsSummaryResponse200>> {
    return this.core.fetch('/growth/marketMaker/maker-rewards-summary', 'get');
  }

  /**
   * Retrieves detailed information about maker rewards.
   *
   */
  getMakerRewardsHistory(metadata?: types.GetMakerRewardsHistoryMetadataParam): Promise<FetchResponse<200, types.GetMakerRewardsHistoryResponse200>> {
    return this.core.fetch('/growth/marketMaker/maker-rewards-detail', 'get', metadata);
  }

  /**
   * Retrieves the whitelist status of a user for market maker activities.
   *
   */
  getUserWhitelistStatusForMarketMaker(): Promise<FetchResponse<200, types.GetUserWhitelistStatusForMarketMakerResponse200>> {
    return this.core.fetch('/growth/marketMaker/whitelist-status', 'get');
  }

  getAffiliateRewardsSummary(): Promise<FetchResponse<200, types.GetAffiliateRewardsSummaryResponse200>> {
    return this.core.fetch('/growth/affiliate/rewards-summary', 'get');
  }

  /**
   * Retrieves user completed trades.
   *
   */
  getUserTrade(metadata?: types.GetUserTradeMetadataParam): Promise<FetchResponse<200, types.GetUserTradeResponse200>> {
    return this.core.fetch('/userTrades', 'get', metadata);
  }

  /**
   * Retrieves user completed trades.
   *
   */
  getUserTradeHistory(metadata?: types.GetUserTradeHistoryMetadataParam): Promise<FetchResponse<200, types.GetUserTradeHistoryResponse200>> {
    return this.core.fetch('/userTradesHistory', 'get', metadata);
  }

  auth(body: types.AuthBodyParam): Promise<FetchResponse<200, types.AuthResponse200>> {
    return this.core.fetch('/authorize', 'post', body);
  }

  countryAuthorization(): Promise<FetchResponse<200, types.CountryAuthorizationResponse200>> {
    return this.core.fetch('/country', 'get');
  }

  isWhitelistedAccount(metadata: types.IsWhitelistedAccountMetadataParam): Promise<FetchResponse<200, types.IsWhitelistedAccountResponse200>> {
    return this.core.fetch('/whitelistedAccount', 'get', metadata);
  }

  updateUserReadOnlyToken(): Promise<FetchResponse<200, types.UpdateUserReadOnlyTokenResponse200>> {
    return this.core.fetch('/generateReadOnlyToken', 'post');
  }

  /**
   * Retrieves user on-chain account information.
   * Specify the parent address if trading as a sub-account.
   *
   */
  getAccount(metadata?: types.GetAccountMetadataParam): Promise<FetchResponse<200, types.GetAccountResponse200>> {
    return this.core.fetch('/account', 'get', metadata);
  }

  /**
   * This method allows users to update the market leverage.
   * All orders for a given market must be placed at the same leverage as the user-set market
   * leverage.
   * This method will force the cancellation of any remaining open orders at the previous
   * market leverage.
   *
   */
  adjustLeverage(body: types.AdjustLeverageBodyParam): Promise<FetchResponse<200, types.AdjustLeverageResponse200>> {
    return this.core.fetch('/account/adjustLeverage', 'post', body);
  }

  /**
   * Allows user to fund gas and USDC tokens on TESTNET
   *
   */
  faucet(body: types.FaucetBodyParam): Promise<FetchResponse<200, types.FaucetResponse200>> {
    return this.core.fetch('/account/faucet', 'post', body);
  }

  /**
   * Allows user to fund gas tokens on TESTNET
   *
   */
  fundGas(): Promise<FetchResponse<200, types.FundGasResponse200>> {
    return this.core.fetch('/account/fundGas', 'post');
  }

  /**
   * Time series data for user's account value over time
   *
   */
  getAccountValueOverTime(metadata: types.GetAccountValueOverTimeMetadataParam): Promise<FetchResponse<200, types.GetAccountValueOverTimeResponse200>> {
    return this.core.fetch('/account/value-graph', 'get', metadata);
  }

  /**
   * Retrieves user account permissions
   *
   */
  getAccountPermissions(metadata: types.GetAccountPermissionsMetadataParam): Promise<FetchResponse<200, types.GetAccountPermissionsResponse200>> {
    return this.core.fetch('/account/getAccountPermissions', 'get', metadata);
  }

  /**
   * Gets verification status of the user account
   *
   */
  verifyDeposit(metadata: types.VerifyDepositMetadataParam): Promise<FetchResponse<200, types.VerifyDepositResponse200>> {
    return this.core.fetch('/account/verifyDeposit', 'get', metadata);
  }
}

const createSDK = (() => { return new SDK(); })()
;

export default createSDK;

export type { AdjustLeverageBodyParam, AdjustLeverageResponse200, AuthBodyParam, AuthResponse200, CountryAuthorizationResponse200, CreateOrderBodyParam, CreateOrderMetadataParam, CreateOrderResponse201, DeleteOrdersResponse200, FaucetBodyParam, FaucetResponse200, FundGasResponse200, GenerateReferralLinkResponse200, GenerateRefferalCodeBodyParam, GenerateRefferalCodeResponse200, GetAccountMetadataParam, GetAccountPermissionsMetadataParam, GetAccountPermissionsResponse200, GetAccountResponse200, GetAccountValueOverTimeMetadataParam, GetAccountValueOverTimeResponse200, GetAffiliatePayoutsMetadataParam, GetAffiliatePayoutsResponse200, GetAffiliateRewardsSummaryResponse200, GetAuxiliaryAddressesResponse200, GetCampaignDetailsResponse200, GetCampaignRewardsMetadataParam, GetCampaignRewardsResponse200, GetCandlestickDataMetadataParam, GetCandlestickDataResponse200, GetContractAddressesMetadataParam, GetContractAddressesResponse200, GetExchangeInfoMetadataParam, GetExchangeInfoResponse200, GetExchangeStatusResponse200, GetFundingRateMetadataParam, GetFundingRateResponse200, GetMakerRewardsHistoryMetadataParam, GetMakerRewardsHistoryResponse200, GetMakerRewardsSummaryResponse200, GetMarketDataMetadataParam, GetMarketDataResponse200, GetMarketSymbolsResponse200, GetMasterInfoMetadataParam, GetMasterInfoResponse200, GetMemberDetailsResponse200, GetMembersMonthlyOverviewMetadataParam, GetMembersMonthlyOverviewResponse200, GetMetaMetadataParam, GetMetaResponse200, GetOpenOrderMetadataParam, GetOpenOrderResponse200, GetOrderMetadataParam, GetOrderResponse200, GetOrderbookMetadataParam, GetOrderbookResponse200, GetOrdersByOrderTypeMetadataParam, GetOrdersByOrderTypeResponse200, GetPartnerDetailsResponse200, GetRecentTradeMetadataParam, GetRecentTradeResponse200, GetRefereeDetailsByPartnerMetadataParam, GetRefereeDetailsByPartnerResponse200, GetRefereeDetailsMetadataParam, GetRefereeDetailsResponse200, GetRefereesCountMetadataParam, GetRefereesCountResponse200, GetReferralDetailsResponse200, GetReferrerInfoMetadataParam, GetReferrerInfoResponse200, GetResponse200, GetTradeAndEarnRewardsDetailMetadataParam, GetTradeAndEarnRewardsDetailResponse200, GetTradeAndEarnRewardsOverviewMetadataParam, GetTradeAndEarnRewardsOverviewResponse200, GetUserFundingHistoryMetadataParam, GetUserFundingHistoryResponse200, GetUserPositionMetadataParam, GetUserPositionResponse200, GetUserRewardsHistoryMetadataParam, GetUserRewardsHistoryResponse200, GetUserRewardsSummaryResponse200, GetUserTradeHistoryMetadataParam, GetUserTradeHistoryResponse200, GetUserTradeMetadataParam, GetUserTradeResponse200, GetUserTransactionHistoryMetadataParam, GetUserTransactionHistoryResponse200, GetUserTransferMetadataParam, GetUserTransferResponse200, GetUserWhitelistStatusForMarketMakerResponse200, IsWhitelistedAccountMetadataParam, IsWhitelistedAccountResponse200, LinkAccountBodyParam, LinkReferredUserBodyParam, LinkReferredUserResponse200, TickerMetadataParam, TickerResponse200, TotalHistoricalTradingRewardsResponse200, UpdateUserReadOnlyTokenResponse200, VerifyDepositMetadataParam, VerifyDepositResponse200 } from './types';
