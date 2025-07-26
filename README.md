# Dividend Portfolio Dashboard

A Streamlit app I built to track and analyze my dividend investments. It helps me understand my portfolio performance and find new dividend stocks to invest in.

## What it does

- **Portfolio Overview**: Shows your current holdings and how they're performing
- **Monthly Analysis**: Breaks down your dividend income by month and spots trends
- **Stock Analysis**: Compare individual stocks and see which ones are working best
- **Dividend Screener**: Find new dividend stocks using Alpha Vantage data
- **Forecast**: Predict future dividend income based on your current holdings
- **Mobile-friendly**: Works well on phones and tablets
- **Secure**: Keeps your API keys safe in environment variables

## Getting Started

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

## Configuration

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

## How it's organized

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

## Development Notes

### Code Quality

I tried to keep the code clean and well-organized:
- Type hints everywhere to make development easier
- Good error handling so users get helpful messages
- Split into modules so it's easier to work with
- Mobile-first design that looks good on any device
- Secure API key handling

### Adding Features

1. Put new features in the right module
2. Document your code well
3. Update config if you add new settings
4. Test on different screen sizes

### Performance

A few things I did to keep it fast:
- Caching with Streamlit's `@st.cache_data`
- Only load data when needed
- Efficient pandas operations
- Respect API rate limits

## Customization

### Styling

You can change how it looks by editing `static/styles.css`:
- Colors and themes
- How it responds to different screen sizes
- Individual component styles
- Dark mode settings

### Adding Data Sources

1. Update the `load_data()` function in `utils.py`
2. Handle any new data format requirements
3. Add caching for the new data

### New APIs

To add other financial data APIs:
- Look at how `dividend_screener.py` does it
- Add your settings to `config.py`
- Make sure errors are handled gracefully

## Troubleshooting

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

## Tips

1. **Data Quality**: Make sure your dividend CSV files are clean and consistent
2. **API Limits**: Alpha Vantage free tier allows 5 calls per minute, so be patient
3. **Browser**: Works best with modern browsers (Chrome, Firefox, Safari, Edge)
4. **Mobile**: Everything should work fine on your phone or tablet

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper documentation
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Thanks

- [Streamlit](https://streamlit.io/) for the amazing framework
- [Alpha Vantage](https://www.alphavantage.co/) for financial data API
- [Plotly](https://plotly.com/) for interactive visualizations