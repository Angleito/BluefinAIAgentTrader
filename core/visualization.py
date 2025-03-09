import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime
import os
import logging
from core.performance_tracker import performance_tracker

logger = logging.getLogger(__name__)

class TradingVisualizer:
    """
    Generate visualizations for trading performance analysis.
    """
    
    def __init__(self, output_dir="visualizations"):
        """
        Initialize the trading visualizer.
        
        Args:
            output_dir: Directory to save visualizations
        """
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def _prepare_trade_data(self):
        """
        Prepare trade data for visualization.
        
        Returns:
            pd.DataFrame: DataFrame with trade data
        """
        closed_trades = performance_tracker.get_closed_positions()
        
        if not closed_trades:
            logger.warning("No closed trades to visualize")
            return None
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(closed_trades)
        
        # Convert string dates to datetime
        df['entry_time'] = pd.to_datetime(df['entry_time'])
        df['exit_time'] = pd.to_datetime(df['exit_time'])
        
        # Sort by exit time
        df = df.sort_values('exit_time')
        
        return df
    
    def plot_equity_curve(self, save=True):
        """
        Plot the equity curve.
        
        Args:
            save: Whether to save the plot to a file
            
        Returns:
            str: Path to the saved file if save=True, None otherwise
        """
        df = self._prepare_trade_data()
        
        if df is None or df.empty:
            return None
        
        # Calculate cumulative P&L
        df['cumulative_pnl'] = df['pnl'].cumsum()
        
        # Create the plot
        plt.figure(figsize=(12, 6))
        plt.plot(df['exit_time'], df['cumulative_pnl'], label='Equity Curve')
        
        # Add a horizontal line at y=0
        plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
        
        # Add labels and title
        plt.xlabel('Date')
        plt.ylabel('Cumulative P&L')
        plt.title('Equity Curve')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Format the date on the x-axis
        plt.gcf().autofmt_xdate()
        
        if save:
            filename = f"{self.output_dir}/equity_curve_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(filename)
            plt.close()
            return filename
        else:
            plt.show()
            plt.close()
            return None
    
    def plot_win_loss_distribution(self, save=True):
        """
        Plot the distribution of winning and losing trades.
        
        Args:
            save: Whether to save the plot to a file
            
        Returns:
            str: Path to the saved file if save=True, None otherwise
        """
        df = self._prepare_trade_data()
        
        if df is None or df.empty:
            return None
        
        # Create a new figure
        plt.figure(figsize=(12, 6))
        
        # Plot histogram of P&L percentages
        plt.hist(df['pnl_percentage'], bins=20, alpha=0.7, color='blue')
        
        # Add labels and title
        plt.xlabel('P&L Percentage')
        plt.ylabel('Number of Trades')
        plt.title('Distribution of Trade P&L')
        plt.grid(True, alpha=0.3)
        
        if save:
            filename = f"{self.output_dir}/pnl_distribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(filename)
            plt.close()
            return filename
        else:
            plt.show()
            plt.close()
            return None
    
    def plot_monthly_performance(self, save=True):
        """
        Plot monthly performance.
        
        Args:
            save: Whether to save the plot to a file
            
        Returns:
            str: Path to the saved file if save=True, None otherwise
        """
        df = self._prepare_trade_data()
        
        if df is None or df.empty:
            return None
        
        # Extract month from exit time
        df['month'] = df['exit_time'].dt.to_period('M')
        
        # Group by month and sum P&L
        monthly_pnl = df.groupby('month')['pnl'].sum()
        
        # Create the plot
        plt.figure(figsize=(12, 6))
        monthly_pnl.plot(kind='bar', color=np.where(monthly_pnl >= 0, 'green', 'red'))
        
        # Add labels and title
        plt.xlabel('Month')
        plt.ylabel('P&L')
        plt.title('Monthly Performance')
        plt.grid(True, alpha=0.3)
        
        # Format the date on the x-axis
        plt.gcf().autofmt_xdate()
        
        if save:
            filename = f"{self.output_dir}/monthly_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(filename)
            plt.close()
            return filename
        else:
            plt.show()
            plt.close()
            return None
    
    def plot_drawdown(self, save=True):
        """
        Plot the drawdown over time.
        
        Args:
            save: Whether to save the plot to a file
            
        Returns:
            str: Path to the saved file if save=True, None otherwise
        """
        df = self._prepare_trade_data()
        
        if df is None or df.empty:
            return None
        
        # Calculate cumulative P&L
        df['cumulative_pnl'] = df['pnl'].cumsum()
        
        # Calculate running maximum
        df['running_max'] = df['cumulative_pnl'].cummax()
        
        # Calculate drawdown
        df['drawdown'] = df['running_max'] - df['cumulative_pnl']
        
        # Create the plot
        plt.figure(figsize=(12, 6))
        plt.plot(df['exit_time'], df['drawdown'], label='Drawdown')
        
        # Add labels and title
        plt.xlabel('Date')
        plt.ylabel('Drawdown')
        plt.title('Drawdown Over Time')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Format the date on the x-axis
        plt.gcf().autofmt_xdate()
        
        if save:
            filename = f"{self.output_dir}/drawdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(filename)
            plt.close()
            return filename
        else:
            plt.show()
            plt.close()
            return None
    
    def generate_performance_report(self):
        """
        Generate a comprehensive performance report with multiple visualizations.
        
        Returns:
            dict: Paths to the generated visualization files
        """
        report_files = {}
        
        # Generate all visualizations
        equity_curve_file = self.plot_equity_curve()
        if equity_curve_file:
            report_files['equity_curve'] = equity_curve_file
        
        win_loss_file = self.plot_win_loss_distribution()
        if win_loss_file:
            report_files['win_loss_distribution'] = win_loss_file
        
        monthly_file = self.plot_monthly_performance()
        if monthly_file:
            report_files['monthly_performance'] = monthly_file
        
        drawdown_file = self.plot_drawdown()
        if drawdown_file:
            report_files['drawdown'] = drawdown_file
        
        # Get performance metrics
        metrics = performance_tracker.get_performance_metrics()
        
        # Create a summary file
        summary_file = f"{self.output_dir}/performance_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(summary_file, 'w') as f:
            f.write("=== TRADING PERFORMANCE SUMMARY ===\n\n")
            f.write(f"Total Trades: {metrics['total_trades']}\n")
            f.write(f"Win Rate: {metrics['win_rate']:.2%}\n")
            f.write(f"Average Profit: {metrics['average_profit']:.2f}\n")
            f.write(f"Average Loss: {metrics['average_loss']:.2f}\n")
            f.write(f"Profit Factor: {metrics['profit_factor']:.2f}\n")
            f.write(f"Total P&L: {metrics['total_pnl']:.2f}\n")
            f.write(f"Maximum Drawdown: {metrics['max_drawdown']:.2f}\n")
        
        report_files['summary'] = summary_file
        
        return report_files

# Create a singleton instance
visualizer = TradingVisualizer() 