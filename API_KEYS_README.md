# API Keys Setup

This document explains how to set up your API keys for the application without storing them in the code files.

## Why This Approach?

GitHub has push protection that prevents you from pushing code with API keys. To avoid this issue, we've replaced all hardcoded API keys with placeholder values in the code files, but the application still needs real API keys to function.

## Option 1: Use the Settings Modal in the Application

The easiest way to set up your API keys is to use the Settings modal in the application:

1. Start the application
2. Click on the Settings icon
3. Enter your API keys in the appropriate fields
4. Click "Save"

The keys will be stored in your browser's localStorage and will be used by the application.

## Option 2: Use the Setup Page

We've created a simple setup page that you can use to set your API keys:

1. Open `setup_keys.html` in your browser
2. Enter your API keys
3. Click "Save Keys"
4. Close the page and start the application

## Option 3: Keep Using the .env File for Backend

The backend will continue to use the API keys from the `.env` file. You only need to set up the keys in localStorage for the frontend.

## Important Notes

- API keys stored in localStorage are only available in your browser
- They are not pushed to GitHub
- They persist between browser sessions until you clear your browser data
- If you're using a different browser or device, you'll need to set up the keys again

## Security Considerations

While this approach prevents API keys from being pushed to GitHub, it's not a secure way to store API keys for production applications. For production, consider using a more secure approach like server-side authentication or a dedicated secrets management service.