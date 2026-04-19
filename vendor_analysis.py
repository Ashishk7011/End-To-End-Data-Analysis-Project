import pandas as pd
import sqlite3
import numpy as np
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from scipy.stats import ttest_ind
import scipy.stats as stats
from format_values import format
from logger import get_logger

warnings.filterwarnings('ignore')

logging = get_logger(__name__, 'Vendor_sales_analysis.log')


class VendorAnalysis:
    """
    A class for performing exploratory data analysis and statistical
    testing on vendor sales data from an inventory database.
    """

    def __init__(self, db_path='inventory.db'):
        self.conn = sqlite3.connect(db_path)
        self.df = None
        self.quality_df = None
        self.vendor_performance = None
        self.top_vendors = None

    # -------------------------------------------------------------------------
    # Data Loading
    # -------------------------------------------------------------------------

    def load_vendor_sales_data(self):
        """Load all records from the vendor_sales_summary table."""
        self.df = pd.read_sql_query('SELECT * FROM vendor_sales_summary', self.conn)
        self.df.to_csv('Final_Analysis_Files/vendor_sales_summary.csv', index=False)
        logging.info('Vendor sales summary data loaded and saved as Final_Analysis_Files/vendor_sales_summary.csv')
        return self.df

    def extract_quality_data(self):
        """Load only rows with positive GrossProfit, TotalSalesQuantity, and ProfitMargin."""
        self.quality_df = pd.read_sql_query(
            '''SELECT *
               FROM vendor_sales_summary
               WHERE GrossProfit > 0
                 AND TotalSalesQuantity > 0
                 AND ProfitMargin > 0''',
            self.conn
        )
        self.quality_df.to_csv('Final_Analysis_Files/vendor_sales_quality_data.csv', index=False)
        logging.info('Quality data extracted and saved as Final_Analysis_Files/vendor_sales_quality_data.csv')
        return self.quality_df

    # -------------------------------------------------------------------------
    # Distribution & EDA Plots
    # -------------------------------------------------------------------------

    def plot_numerical_hist_distributions(self, df=None):
        """Plot histograms with KDE for all numerical columns."""
        df = df if df is not None else self.quality_df
        numerical_cols = df.select_dtypes(exclude=['object']).columns

        fig, axes = plt.subplots(4, 4, figsize=(15, 10))
        axes = axes.flatten()
        for i, col in enumerate(numerical_cols):
            plt.subplot(4, 4, i + 1)
            sns.histplot(df[col], kde=True, bins=30, ax=axes[i])
            plt.title(f'Distribution of {col}') 
        plt.tight_layout()
        plt.savefig('Images/plot_numerical_hist_distributions.png')
        logging.info('Numerical histograms with KDE saved as Images/plot_numerical_hist_distributions.png')
        plt.show(block = False)
        plt.pause(1)   # show for 1 seconds
        plt.close()

    def plot_numericals_boxplots(self, df=None):
        """Plot boxplots for all numerical columns to detect outliers."""
        df = df if df is not None else self.df
        numerical_cols = df.select_dtypes(exclude=['object']).columns

        fig, axes = plt.subplots(4, 4, figsize=(15, 10))
        axes = axes.flatten()

        for i, col in enumerate(numerical_cols):
            sns.boxplot(y=df[col], ax=axes[i])
            axes[i].set_title(f'Boxplot of {col}')
        plt.tight_layout()
        plt.savefig('Images/plot_numericals_boxplots.png')
        plt.show(block = False)
        plt.pause(1)   # show for 1 seconds
        plt.close()
        logging.info('Numerical boxplots saved as Images/plot_numericals_boxplots.png')

    def plot_categorical_counts(self, df=None):
        """Plot count plots for all categorical columns (top 10 categories each)."""
        df = df if df is not None else self.quality_df
        categorical_cols = df.select_dtypes(include=['object']).columns

        fig, axes = plt.subplots(1, 2, figsize=(15, 10))
        axes = axes.flatten()
        for i, col in enumerate(categorical_cols):
            sns.countplot(y=df[col], order=df[col].value_counts().index[:10], ax=axes[i])
            axes[i].set_title(f'Countplot of {col}')

        plt.tight_layout()
        plt.savefig('Images/plot_categorical_counts.png')
        logging.info('Categorical count plots saved as Images/plot_categorical_counts.png')
        plt.show(block = False)
        plt.pause(1)   # show for 1 seconds
        plt.close()

    def plot_correlation_heatmap(self, df=None):
        """Plot a correlation heatmap of all numerical features."""
        df = df if df is not None else self.quality_df
        numerical_cols = df.select_dtypes(exclude=['object']).columns

        fig,ax = plt.subplots(figsize=(12, 10))
        correlation_matrix = df[numerical_cols].corr()
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', linewidths=0.5)
        plt.title('Correlation Matrix of Numerical Features')
        plt.savefig('Images/plot_correlation_heatmap.png')
        plt.show(block = False)
        plt.pause(1)   # show for 1 seconds
        plt.close()
        logging.info('Correlation heatmap saved as Images/plot_correlation_heatmap.png')
    # -------------------------------------------------------------------------
    # Brand Analysis
    # -------------------------------------------------------------------------

    def brand_performance_data(self, df=None):
        """
        Identify brands with low sales but high profit margins and plot them
        against all other brands.

        Returns the filtered brand_performance DataFrame (sales < $10,000).
        """
        df = df if df is not None else self.quality_df

        brand_performance = df.groupby('Description').agg(
            {'TotalSalesDollars': 'sum', 'ProfitMargin': 'sum'}
        ).reset_index()

        low_sales_threshold = brand_performance['TotalSalesDollars'].quantile(0.15)
        high_margin_threshold = brand_performance['ProfitMargin'].quantile(0.85)

        print(f'Low Sales Threshold: {low_sales_threshold}')
        print(f'High Profit Margin Threshold: {high_margin_threshold}')

        target_brands = brand_performance[
            (brand_performance['TotalSalesDollars'] <= low_sales_threshold) &
            (brand_performance['ProfitMargin'] >= high_margin_threshold)
        ]
        print("Brands with Low Sales but High Profit Margins:")
        print(target_brands.sort_values('TotalSalesDollars'))

        brand_performance_filtered = brand_performance[
            brand_performance['TotalSalesDollars'] < 10000
        ]

        brand_performance.to_csv('Final_Analysis_Files/brand_performance.csv', index=False)
        logging.info('Brand performance data saved as Final_Analysis_Files/brand_performance.csv')

        plt.figure(figsize=(15, 6))
        sns.scatterplot(
            data=brand_performance_filtered,
            x='TotalSalesDollars', y='ProfitMargin',
            color='blue', label='All Brands', alpha=0.2
        )
        sns.scatterplot(
            data=target_brands,
            x='TotalSalesDollars', y='ProfitMargin',
            color='red', label='Target Brands'
        )
        plt.axhline(high_margin_threshold, linestyle='-', color='black', label='High Margin Threshold')
        plt.axvline(low_sales_threshold, linestyle='-', color='black', label='Low Sales Threshold')
        plt.xlabel('Total Sales ($)')
        plt.ylabel('Profit Margin (%)')
        plt.title(
            'Brands for Promotional or Pricing Adjustments '
            '(inc. Brands having sales less than $10,000 for better visuals)'
        )
        plt.legend()
        plt.grid(True)
        plt.savefig('Images/brand_performance_scatter.png')
        plt.show(block = False)
        plt.pause(1)   # show for 1 seconds
        plt.close()
        logging.info('Brand performance scatter plot saved as Images/brand_performance_scatter.png')

        return brand_performance

    # -------------------------------------------------------------------------
    # Vendor Analysis
    # -------------------------------------------------------------------------

    def plot_top_vendors_brands(self, df=None):
        """Bar charts for the top 10 vendors and top 10 brands by total sales."""
        df = df if df is not None else self.quality_df

        top_vendors = df.groupby('VendorName')['TotalSalesDollars'].sum().nlargest(10)
        top_brands = df.groupby('Description')['TotalSalesDollars'].sum().nlargest(10)
 
        plt.figure(figsize=(15, 10))
        plt.subplot(1, 2, 1)
        ax1 = sns.barplot(y=top_vendors.index, x=top_vendors.values, palette='Blues_r')
        plt.title('Top 10 Vendors by Sales')
        for bar in ax1.patches:
            ax1.text(
                bar.get_width() + bar.get_width() * 0.02,
                bar.get_y() + bar.get_height() / 2,
                format(bar.get_width()),
                ha='left', va='center', fontsize=10, color='black'
            )

        plt.subplot(1, 2, 2)
        ax2 = sns.barplot(y=top_brands.index.astype(str), x=top_brands.values, palette='Reds_r')
        plt.title('Top 10 Brands by Sales')
        for bar in ax2.patches:
            ax2.text(
                bar.get_width() + bar.get_width() * 0.02,
                bar.get_y() + bar.get_height() / 2,
                format(bar.get_width()),
                ha='left', va='center', fontsize=10, color='black'
            )

        plt.tight_layout()
        plt.savefig('Images/top_vendors_brands.png')
        plt.show(block = False)
        plt.pause(1)   # show for 1 seconds
        plt.close()
        logging.info('Top vendors and brands bar charts saved as Images/top_vendors_brands.png')

    def vendor_performance_data(self, df=None):
        """
        Aggregate vendor-level purchase, profit, and sales totals and compute
        each vendor's purchase contribution percentage.

        Stores and returns the vendor_performance DataFrame.
        """
        df = df if df is not None else self.quality_df

        self.vendor_performance = df.groupby('VendorName').agg(
            {
                'TotalPurchaseDollars': 'sum',
                'GrossProfit': 'sum',
                'TotalSalesDollars': 'sum',
            }
        ).reset_index()

        self.vendor_performance['PurchaseContribution%'] = (
            self.vendor_performance['TotalPurchaseDollars']
            / self.vendor_performance['TotalPurchaseDollars'].sum()
        ) * 100
        logging.info('Vendor performance data aggregated.')
        self.vendor_performance.to_csv('Final_Analysis_Files/vendor_performance.csv', index=False)
        logging.info('Vendor performance data saved as Final_Analysis_Files/vendor_performance.csv')

        return self.vendor_performance

    def top_vendors_performance(self, vendor_performance=None):
        """
        Plot a Pareto chart showing purchase contribution % and cumulative %
        for the top 10 vendors.

        Returns the top 10 vendor DataFrame.
        """
        vendor_performance = vendor_performance if vendor_performance is not None else self.vendor_performance

        vendor_performance= round(vendor_performance.sort_values('PurchaseContribution%', ascending=False), 2)

        self.top_vendors = vendor_performance.head(10).copy()
        self.top_vendors['TotalSalesDollars'] = self.top_vendors['TotalSalesDollars'].apply(format)
        self.top_vendors['TotalPurchaseDollars'] = self.top_vendors['TotalPurchaseDollars'].apply(format)
        self.top_vendors['GrossProfit'] = self.top_vendors['GrossProfit'].apply(format)

        self.top_vendors['cumulative_contribution%']= self.top_vendors['PurchaseContribution%'].cumsum()

        fig, ax1 = plt.subplots(figsize=(10, 6))
        sns.barplot(
            x=self.top_vendors['VendorName'],
            y=self.top_vendors['PurchaseContribution%'],
            palette='rocket',
            ax=ax1
        )

        for i, value in enumerate(self.top_vendors['PurchaseContribution%']):
            ax1.text(i, value - 1, str(value) + '%', ha='center', fontsize=10, color='white')

        ax2 = ax1.twinx()
        ax2.plot(
            self.top_vendors['VendorName'],
            self.top_vendors['cumulative_contribution%'],
            color='red', marker='o', linestyle='dashed', label='cumulative_contribution%'
        )

        ax1.set_xticklabels(self.top_vendors['VendorName'], rotation=90)
        ax1.set_ylabel('Purchase Contribution %', color='blue')
        ax2.set_ylabel('Cumulative Contribution %', color='red')
        ax1.set_xlabel('Vendors')
        ax1.set_title('Pareto Chart: Vendor Contribution to Total Purchases')
        ax2.axhline(y=100, color='gray', linestyle='dashed', alpha=0.7)
        ax2.legend(loc='upper right')
        plt.savefig('Images/top_vendors_pareto.png')
        logging.info('Top vendors Pareto chart saved as Images/top_vendors_pareto.png')
        plt.show(block = False)
        plt.pause(1)   # show for 1 seconds
        plt.close()
        logging.info('\n'+'Top 10 vendors performance data:\n' + self.top_vendors.to_string(index=False) + '\n\n')
        return self.top_vendors

    def plot_top_vendors_donut_chart(self, top_vendors=None):
        """Donut chart showing purchase contribution of top 10 vendors vs others."""
        top_vendors = top_vendors if top_vendors is not None else self.top_vendors

        vendors = list(top_vendors['VendorName'].values)
        purchase_contributions = list(top_vendors['PurchaseContribution%'].values)
        total_contribution = sum(purchase_contributions)
        remaining_contribution = 100 - total_contribution

        vendors.append('Other Vendors')
        purchase_contributions.append(remaining_contribution)

        fig, ax = plt.subplots(figsize=(8, 8))
        wedges, texts, autotexts = ax.pie(
            purchase_contributions,
            labels=vendors,
            autopct='%1.1f%%',
            startangle=140,
            pctdistance=0.85,
            colors=plt.cm.Paired.colors
        )

        centre_circle = plt.Circle((0, 0), 0.70, fc='white')
        ax.add_artist(centre_circle)

        ax.text(
            0, 0,
            f'Top 10 Total:\n{total_contribution:.2f}%',
            fontsize=14, fontweight='bold', ha='center', va='center'
        )
        ax.set_title('Purchase Contribution of Top 10 Vendors vs Others')
        plt.savefig('Images/top_vendors_donut_chart.png')
        plt.show(block = False)
        plt.pause(1)   # show for 1 seconds
        plt.close()
        logging.info('Top vendors donut chart saved as Images/top_vendors_donut_chart.png')

    # -------------------------------------------------------------------------
    # Pricing & Inventory
    # -------------------------------------------------------------------------
    def low_stock_turnover_vendors(self, df=None):
        """Identify vendors with low stock turnover."""
        df = df if df is not None else self.quality_df
        low_turnover_vendors = df[df['StockTurnover'] < 1].groupby('VendorName')[['StockTurnover']].mean().sort_values('StockTurnover')
        logging.info('\n'+'Vendors with low stock turnover:\n' + low_turnover_vendors.head(10).to_string() + '\n\n')
        low_turnover_vendors.to_csv('Final_Analysis_Files/low_stock_turnover_vendors.csv')
        logging.info('Low stock turnover vendors saved as Final_Analysis_Files/low_stock_turnover_vendors.csv')

        return low_turnover_vendors


    def plot_unit_price_by_order_size(self, df=None):       
        """Boxplot of unit price segmented by order size (Small / Medium / Large)."""
        df = df if df is not None else self.quality_df

        df = df.copy()
        df['unitprice'] = df['TotalPurchaseDollars'] / df['TotalPurchaseQuantity']
        df['OrderSize'] = pd.qcut(df['TotalPurchaseQuantity'], q=3, labels=['Small', 'Medium', 'Large'])

        plt.figure(figsize=(8, 6))
        sns.boxplot(x='OrderSize', y='unitprice', data=df, palette='viridis')
        plt.title('Average Unit Price by Order Size')
        plt.savefig('Images/unit_price_by_order_size.png')
        logging.info('Unit price by order size boxplot saved as Images/unit_price_by_order_size.png')
        plt.show(block = False)
        plt.pause(1)   # show for 1 seconds
        plt.close()

    def inventory_turnover_analysis(self, df=None):
        """
        Calculate unsold inventory value per vendor and print the top 10
        vendors with the most capital locked in unsold stock.
        """
        df = df if df is not None else self.quality_df

        df = df.copy()
        df['UnsoldInventoryValue'] = (
            (df['TotalPurchaseQuantity'] - df['TotalSalesQuantity']) * df['PurchasePrice']
        )

        print('Total unsold inventory value across all vendors: $', format(df['UnsoldInventoryValue'].sum()))

        inventory_value_per_vendor = (
            df.groupby('VendorName')['UnsoldInventoryValue']
            .sum()
            .reset_index()
            .sort_values(by='UnsoldInventoryValue', ascending=False)
        )
        inventory_value_per_vendor = inventory_value_per_vendor[inventory_value_per_vendor['UnsoldInventoryValue'] >= 0]
        inventory_value_per_vendor['UnsoldInventoryValue'] = (
            inventory_value_per_vendor['UnsoldInventoryValue'].apply(format)
        )
        

        logging.info('\n'+'Top 10 vendors with the most capital locked in unsold stock:\n' + inventory_value_per_vendor.head(10).to_string(index=False) + '\n\n')
        inventory_value_per_vendor.to_csv('Final_Analysis_Files/unsold_inventory_value_per_vendor.csv', index=False)
        logging.info('Unsold inventory value per vendor saved as Final_Analysis_Files/unsold_inventory_value_per_vendor.csv')

    # -------------------------------------------------------------------------
    # Statistical Analysis
    # -------------------------------------------------------------------------

    @staticmethod
    def confidence_interval(data, confidence=0.95):
        """
        Calculate the mean and confidence interval for a data series.

        Returns (mean, lower_bound, upper_bound).
        """
        mean_val = np.mean(data)
        std_err = np.std(data, ddof=1) / np.sqrt(len(data))
        t_critical = stats.t.ppf((1 + confidence) / 2, df=len(data) - 1)
        margin_of_error = t_critical * std_err
        logging.info(f'Confidence interval calculated: Mean={mean_val:.2f}, Margin of Error={margin_of_error:.2f}')
        return mean_val, mean_val - margin_of_error, mean_val + margin_of_error

    def confidence_interval_comparison(self, df=None):
        """
        Compare 95% confidence intervals for profit margins of
        top-performing vs low-performing vendors and plot distributions.

        Stores top_vendors_data and low_vendors_data as instance attributes
        for downstream use (e.g. t-test).
        """
        df = df if df is not None else self.quality_df

        top_threshold = df['TotalSalesDollars'].quantile(0.75)
        low_threshold = df['TotalSalesDollars'].quantile(0.25)

        self.low_vendors_data = df[df['TotalSalesDollars'] <= low_threshold]['ProfitMargin'].dropna()
        self.top_vendors_data = df[df['TotalSalesDollars'] >= top_threshold]['ProfitMargin'].dropna()

        top_mean, top_lower, top_upper = self.confidence_interval(self.top_vendors_data)
        low_mean, low_lower, low_upper = self.confidence_interval(self.low_vendors_data)

        logging.info(f"Top Vendors 95% CI: ({top_lower:.2f}, {top_upper:.2f}), Mean: {top_mean:.2f}")
        logging.info(f"Low Vendors 95% CI: ({low_lower:.2f}, {low_upper:.2f}), Mean: {low_mean:.2f}")

        fig, ax = plt.subplots(figsize=(10, 6))

        sns.histplot(self.top_vendors_data, kde=True, color='blue', bins=30, alpha=0.5, label='Top Vendors',ax=ax)
        ax.axvline(top_lower, color='blue', linestyle='--', label=f'Top Lower: {top_lower:.2f}')
        ax.axvline(top_upper, color='blue', linestyle='--', label=f'Top Upper: {top_upper:.2f}')
        ax.axvline(top_mean,  color='blue', linestyle='-',  label=f'Top Mean: {top_mean:.2f}')

        sns.histplot(self.low_vendors_data, kde=True, color='red', bins=30, alpha=0.5, label='Low Vendors',ax=ax)
        ax.axvline(low_lower, color='red', linestyle='--', label=f'Low Lower: {low_lower:.2f}')
        ax.axvline(low_upper, color='red', linestyle='--', label=f'Low Upper: {low_upper:.2f}')
        ax.axvline(low_mean,  color='red', linestyle='-',  label=f'Low Mean: {low_mean:.2f}')

        ax.set_title('Confidence Interval Comparison: Top vs. Low Vendors (Profit Margin)')
        ax.set_xlabel('Profit Margin (%)')
        ax.set_ylabel('Frequency')
        ax.legend()
        ax.grid(True)
        plt.savefig('Images/confidence_interval_comparison.png')
        plt.show(block = False)
        plt.pause(1)   # show for 1 seconds
        plt.close()
        logging.info('Confidence interval comparison plot saved as Images/confidence_interval_comparison.png')

    def t_test_comparison(self):
        """
        Perform a Welch's two-sample t-test comparing profit margins of
        top vs low vendors.

        Requires confidence_interval_comparison() to be called first.
        """
        if not hasattr(self, 'top_vendors_data') or not hasattr(self, 'low_vendors_data'):
            raise RuntimeError("Run confidence_interval_comparison() before t_test_comparison().")

        t_stat, p_value = ttest_ind(self.top_vendors_data, self.low_vendors_data, equal_var=False)

        logging.info(f"T-Statistic: {t_stat:.4f}, P-Value: {p_value:.4f}")
        if p_value < 0.05:
            logging.info("Reject H0: There is a significant difference in profit margins between top and low-performing vendors.")
        else:
            logging.info("Fail to Reject H0: No significant difference in profit margins.")

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def close(self):
        """Close the database connection."""
        self.conn.close()
        logging.info('Database connection closed.')


# -----------------------------------------------------------------------------
# Example usage
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    analysis = VendorAnalysis(db_path='inventory.db')
    logging.info('Vendor analysis started.')
    df = analysis.load_vendor_sales_data()
    logging.info('Vendor sales data loaded successfully.')
    analysis.extract_quality_data()
    analysis.plot_numerical_hist_distributions()
    analysis.plot_numericals_boxplots()
    analysis.plot_categorical_counts()
    analysis.plot_correlation_heatmap()
    analysis.brand_performance_data()
    analysis.plot_top_vendors_brands()

    vendor_perf = analysis.vendor_performance_data()
    top_v = analysis.top_vendors_performance(vendor_perf)
    analysis.plot_top_vendors_donut_chart(top_v)
    analysis.low_stock_turnover_vendors()
    analysis.plot_unit_price_by_order_size()
    analysis.inventory_turnover_analysis()

    analysis.confidence_interval_comparison()
    analysis.t_test_comparison()

    analysis.close()
