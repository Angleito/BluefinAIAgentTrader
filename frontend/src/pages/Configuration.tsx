import React, { useState, useEffect } from 'react';
import { getConfiguration, updateConfiguration } from '../api';

interface ConfigType {
  TRADING_PARAMS: {
    symbol?: string;
    timeframe?: string;
    leverage?: number;
    // Other TRADING_PARAMS fields...
  };
  RISK_PARAMS: {
    max_risk_per_trade?: number;
    // Other RISK_PARAMS fields...
  };
  AI_PARAMS: {
    use_perplexity?: boolean;
    // Other AI_PARAMS fields...
  };
}

interface ApiResponse {
  status: string;
  message: string;
  [key: string]: any;
}

const Configuration: React.FC = () => {
  const [config, setConfig] = useState<ConfigType>({
    TRADING_PARAMS: {},
    RISK_PARAMS: {},
    AI_PARAMS: {}
  });

  useEffect(() => {
    // Fetch current configuration on component mount
    getConfiguration().then((response) => {
      if (response && typeof response === 'object' && 'TRADING_PARAMS' in response) {
        setConfig(response as ConfigType);
      }
    });
  }, []);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const result = await updateConfiguration(config) as ApiResponse;
    alert(result.message);
    // Refetch configuration after successful update
    getConfiguration().then((response) => {
      if (response && typeof response === 'object' && 'TRADING_PARAMS' in response) {
        setConfig(response as ConfigType);
      }
    });
  };

  return (
    <div>
      <h1>Agent Configuration</h1>
      <form onSubmit={handleSubmit}>
        <section>
          <h2>Trading Parameters</h2>
          <label>
            Symbol:
            <input 
              type="text"
              value={config.TRADING_PARAMS.symbol || ''}
              onChange={e => setConfig({
                ...config,
                TRADING_PARAMS: {
                  ...config.TRADING_PARAMS, 
                  symbol: e.target.value
                }
              })}
            />
          </label>
          <label>
            Timeframe:
            <input
              type="text" 
              value={config.TRADING_PARAMS.timeframe || ''}
              onChange={e => setConfig({
                ...config,
                TRADING_PARAMS: {
                  ...config.TRADING_PARAMS,
                  timeframe: e.target.value
                }
              })}
            />
          </label>
          <label>
            Leverage:
            <input
              type="number"
              value={config.TRADING_PARAMS.leverage || 0}
              onChange={e => setConfig({
                ...config,
                TRADING_PARAMS: {
                  ...config.TRADING_PARAMS,
                  leverage: parseInt(e.target.value)
                }
              })}
            />
          </label>
          {/* Other TRADING_PARAMS fields... */}
        </section>

        <section>
          <h2>Risk Parameters</h2>
          <label>
            Max Risk Per Trade:
            <input
              type="number"
              step="0.01"
              value={config.RISK_PARAMS.max_risk_per_trade || 0}
              onChange={e => setConfig({
                ...config,
                RISK_PARAMS: {
                  ...config.RISK_PARAMS,
                  max_risk_per_trade: parseFloat(e.target.value)
                }
              })}
            />
          </label>
          {/* Other RISK_PARAMS fields... */}
        </section>
        
        <section>
          <h2>AI Parameters</h2>
          <label>
            Use Perplexity:
            <input
              type="checkbox"
              checked={config.AI_PARAMS.use_perplexity || false}
              onChange={e => setConfig({
                ...config,
                AI_PARAMS: {
                  ...config.AI_PARAMS,
                  use_perplexity: e.target.checked
                }
              })}
            />
          </label>
          {/* Other AI_PARAMS fields... */}  
        </section>

        <button type="submit">Save Changes</button>
      </form>
    </div>
  );
};

export default Configuration;
