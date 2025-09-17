# Microsoft Learning Module Formatter

A Flask web application that reformats Microsoft Learning modules into a clean, reader-friendly format while preserving navigation and content structure.

## Features

- **Clean Reading Experience**: Removes clutter and provides better typography for extended reading
- **Preserved Navigation**: Maintains module structure with sidebar navigation
- **Image Support**: Properly displays images and diagrams from Microsoft Learn
- **Table Formatting**: Preserves and styles tables appropriately
- **Mobile Responsive**: Works on desktop and mobile devices
- **Real-time Loading**: Uses HTMX for seamless content loading without page refreshes

## Requirements

- Python 3.7+
- Flask
- BeautifulSoup4
- Requests

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mslearn-reader
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create the templates directory and add template files:
```
mslearn-reader/
├── app.py
├── requirements.txt
└── templates/
    ├── index.html
    ├── navigation.html
    └── content.html
```

## Usage

1. Start the Flask development server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Enter a Microsoft Learning module URL in the format:
```
https://learn.microsoft.com/en-us/training/modules/[module-name]/
```

4. Click "Load Module" to fetch and format the content

5. Use the sidebar navigation to browse through different sections

## How It Works

The application:

1. **Fetches Module Structure**: Parses the main module page to extract navigation links
2. **Loads Individual Sections**: Fetches each unit/section page separately
3. **Cleans Content**: Removes unnecessary elements while preserving text, images, and tables
4. **Fixes URLs**: Converts relative image and link URLs to absolute URLs
5. **Applies Styling**: Uses clean typography and layout for better readability

## Architecture

- **MSLearnParser Class**: Core parsing logic for extracting and cleaning content
- **Flask Routes**: Web interface for loading modules and sections
- **HTMX Integration**: Real-time content updates without page refreshes
- **Template System**: Modular HTML templates for different components

## Configuration

The application includes several configurable aspects:

- **Typography**: Warm beige background (#faf8f5) for reduced eye strain
- **Content Cleaning**: Removes navigation, headers, footers while preserving main content
- **Image Processing**: Handles Microsoft Learn's relative path structure
- **Debug Logging**: Comprehensive logging for troubleshooting

## Troubleshooting

### No Content Loading
- Check console output for debug information
- Verify the Microsoft Learn URL is valid
- Ensure network connectivity

### Images Not Displaying
- Check browser developer tools for failed image requests
- Verify image URLs are being converted correctly in console output

### Navigation Not Working
- Restart Flask server if templates were modified
- Clear browser cache for CSS/JS changes

## Development

### Adding Debug Output
The application includes extensive debug logging. Check the console output for:
- Module parsing information
- Image URL conversion details
- Section loading progress
- Error messages and stack traces

### Modifying Templates
- Edit files in the `templates/` directory
- Restart Flask server for changes to take effect
- Use hard refresh (Ctrl+F5) to clear browser cache

## Limitations

- Only works with Microsoft Learning modules
- Requires internet connection to fetch content
- Some advanced interactive elements may not be preserved
- Content is fetched in real-time (no caching)

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]