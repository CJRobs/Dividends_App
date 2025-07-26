# 📊 Dividend Portfolio Dashboard

A comprehensive Streamlit application for tracking, analyzing, and forecasting dividend income with advanced screening capabilities.

## ✨ Features

- **📈 Portfolio Overview**: Real-time dashboard with key metrics and performance summaries
- **📅 Monthly Analysis**: Detailed monthly breakdown and trend analysis
- **🏢 Stock Analysis**: Individual stock performance evaluation and comparison
- **🔍 Dividend Screener**: Advanced stock screening with Alpha Vantage integration
- **🔮 Forecast**: Predictive modeling for future dividend income
- **📱 Responsive Design**: Mobile-friendly interface with modern styling
- **🔐 Security**: Environment-based API key management

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Alpha Vantage API key (free at [alphavantage.co](https://www.alphavantage.co/support/#api-key))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd dividends
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys and settings
   ```

4. **Run the application**
   ```bash
   streamlit run dividend_app.py
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required
ALPHA_VANTAGE_API_KEY=your_api_key_here

# Optional (with defaults)
DEFAULT_CURRENCY=GBP
DEFAULT_THEME=Light
DEFAULT_FORECAST_MONTHS=12
CACHE_TTL_HOURS=1
```

### Data Sources

The application expects dividend data in CSV format in the `dividends/` directory. The data should include columns:
- `Time`: Date of dividend payment
- `Name`: Company/stock name
- `Total`: Dividend amount

## 📁 Project Structure

```
dividends/
├── dividend_app.py          # Main application entry point
├── config.py               # Configuration management
├── utils.py                # Utility functions and common code
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── static/
│   └── styles.css         # Enhanced responsive CSS
├── tabs/                  # Tab modules
│   ├── __init__.py       # Package initialization
│   ├── overview.py       # Portfolio overview tab
│   ├── monthly_analysis.py  # Monthly analysis tab
│   ├── stock_analysis.py    # Stock analysis tab
│   ├── dividend_screener.py # Dividend screening tab
│   └── forecast.py          # Forecasting tab
└── dividends/             # Data directory
    └── *.csv             # Dividend data files
```

## 🛠️ Development

### Code Quality

The codebase follows modern Python practices:
- **Type hints** throughout for better IDE support
- **Comprehensive error handling** with user-friendly messages
- **Modular architecture** with separation of concerns
- **Responsive design** with mobile-first approach
- **Security best practices** for API key management

### Adding New Features

1. Create new functionality in appropriate modules
2. Add comprehensive docstrings and type hints
3. Update configuration if needed
4. Test thoroughly across different screen sizes

### Performance Optimization

The application uses several optimization techniques:
- **Smart caching** with `@st.cache_data` decorators
- **Lazy loading** of expensive operations
- **Efficient data processing** with pandas
- **Rate limiting** for API calls

## 🔧 Customization

### Themes and Styling

Modify `static/styles.css` to customize:
- Color schemes and themes
- Responsive breakpoints
- Component styling
- Dark mode preferences

### Adding New Data Sources

1. Extend the `load_data()` function in `utils.py`
2. Update data preprocessing logic
3. Add new cache keys if needed

### API Integration

The application is designed to easily integrate new data sources:
- Follow the pattern in `dividend_screener.py`
- Add configuration options in `config.py`
- Implement proper error handling

## 🐛 Troubleshooting

### Common Issues

**API Key Errors**
- Ensure your `.env` file exists and contains a valid API key
- Check API key permissions and rate limits

**Data Loading Issues**
- Verify CSV files are in the correct format
- Check file permissions and paths

**Performance Issues**
- Clear Streamlit cache: Menu → Clear Cache
- Reduce data size or adjust cache TTL

### Debug Mode

Run with debug logging:
```bash
streamlit run dividend_app.py --logger.level=debug
```

## 📊 Usage Tips

1. **Data Quality**: Ensure your dividend data is clean and consistent
2. **API Limits**: Be mindful of Alpha Vantage rate limits (5 calls/minute for free tier)
3. **Browser Compatibility**: Use modern browsers for best experience
4. **Mobile Usage**: The interface is optimized for mobile devices

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper documentation
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) for the amazing framework
- [Alpha Vantage](https://www.alphavantage.co/) for financial data API
- [Plotly](https://plotly.com/) for interactive visualizations