from pyexpat import features

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta


class MLService:
    def __init__(self, market_service):
        self.market_service = market_service
        self.model = {} #cache for trained models

    # Predicting stock movement  method
    def predict_stock_movement(self, symbols, days=30):
        #Predicting stock price movements for the given symbols
        predictions = {}

        for symbol in symbols:
            try:
                #Getting Historical Data
                historical_data = self._get_historical_data(symbol)

                if historical_data is None or len(historical_data) < 30:
                    print(f"Not enough historical data for {symbol}")
                    continue

                #Generating Features
                features = self._generate_features(historical_data)

                if features is None:
                    print(f"Failed to generate features for {symbol}")
                    continue


                print(f"Feature columns for {symbol}: {features.columns.tolist()}")

                #Making the Prediction
                expected_return, target_price, confidence = self._predict_return(symbol, features, days)

                predictions[symbol] = {
                    'expected_return': expected_return,
                    'target_price': target_price,
                    'confidence': confidence
                }
            except Exception as e:
                print(f"Error predicting stock movement for {symbol}: {e}")

        return predictions

#Historical data method
    def _get_historical_data(self, symbol, period='200d'):
        #Getting historical price data for a symbol
        try:
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'apikey': self.market_service.api_key,
                'outputsize': 'full'
            }

            import requests
            response = requests.get(self.market_service.base_url, params=params)
            result = response.json()

            if 'Time Series (Daily)' in result:
                #Converting Data to Dataframe
                time_series = result['Time Series (Daily)']
                data_points = []

                for date_str, values in time_series.items():
                    data_points.append({
                        'date': date_str,
                        'open': float(values['1. open']),
                        'high': float(values['2. high']),
                        'low': float(values['3. low']),
                        'close': float(values['4. close']),
                        'volume': float(values['5. volume'])
                    })

                df = pd.DataFrame(data_points)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')

                print(f"Retrieved {len(df)} rows of historical data for {symbol}")
                return df

            print(f"No Time Series data found for {symbol}")
            return None

        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return None

    # Generate Feature method
    def _generate_features(self, df):
        """Generating features for prediction model"""
        print(f"Generating features. DataFrame shape: {df.shape}")
        print(f"DataFrame columns: {df.columns.tolist()}")

        df_copy = df.copy()

        try:
            # Generating features for prediction model
            #returns
            df_copy['return_1d'] = df_copy['close'].pct_change(1)
            df_copy['return_5d'] = df_copy['close'].pct_change(5)

            #Moving averages
            df_copy['sma_5'] = df_copy['close'].rolling(window=5).mean()
            df_copy['sma_20'] = df_copy['close'].rolling(window=20).mean()

            #Rsi calculation
            df_copy['rsi_14'] = self._calculate_rsi(df_copy['close'], 14)

            #Volatility
            df_copy['volatility'] = df_copy['return_1d'].rolling(window=20).std()

            # Nan Values drop
            df_copy = df_copy.dropna()

            print(f"After feature generation. DataFrame shape: {df_copy.shape}")
            print(f"DataFrame columns: {df_copy.columns.tolist()}")

            return df_copy

        except Exception as e:
            print(f"Error generating features: {str(e)}")

            return df

    #Rsi Calculation Method
    def _calculate_rsi(self, prices, period=14):
        delta = prices.diff()

        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0
        down = down.abs()

        avg_gain = up.rolling(window=period).mean()
        avg_loss = down.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _predict_return(self, symbol, df, days=30):
        """Predict future returns based on historical data"""
        print(f"Starting prediction for {symbol} with {len(df)} rows of data")

        if len(df) < 30:
            print(f"Not enough data for {symbol}, returning defaults")
            return 0, 0, 0

        try:
            # Calculate recent return as a baseline prediction
            if 'return_5d' in df.columns:
                recent_return = df['return_5d'].dropna().mean() * (days / 5)
            else:
                recent_return = 0

            current_price = df['close'].iloc[-1]

            # Print key data points for debugging
            print(f"Current price for {symbol}: {current_price}")
            print(f"Recent return for {symbol}: {recent_return}")

            # For more advanced prediction, we need at least 60 days of data
            if len(df) < 60:
                print(f"Not enough data for advanced prediction for {symbol}, using simple model")
                target_price = current_price * (1 + recent_return)
                return recent_return, target_price, 0.5

            # Create target variable - future 30-day return
            df = df.copy()  # Avoid SettingWithCopyWarning
            df['target'] = df['close'].shift(-30) / df['close'] - 1

            # Select features for prediction - make sure they all exist
            possible_features = ['sma_5', 'sma_20', 'rsi_14', 'return_1d', 'return_5d', 'volatility']
            features = [f for f in possible_features if f in df.columns]

            if not features:
                print(f"No valid features for {symbol}, using simple model")
                target_price = current_price * (1 + recent_return)
                return recent_return, target_price, 0.5

            print(f"Using features for {symbol}: {features}")

            # Remove NaN values
            df = df.dropna(subset=features + ['target'])

            if len(df) < 30:
                print(f"Not enough clean data for {symbol} after removing NaNs")
                target_price = current_price * (1 + recent_return)
                return recent_return, target_price, 0.5

            # Prepare training data - use most data except the last 30 days
            X = df[features].iloc[:-30]
            y = df['target'].iloc[:-30]

            print(f"Training data shape for {symbol}: {X.shape}, {y.shape}")

            if len(X) < 10:
                print(f"Not enough training data for {symbol}")
                target_price = current_price * (1 + recent_return)
                return recent_return, target_price, 0.5

            # Fit the linear regression model
            from sklearn.linear_model import LinearRegression
            model = LinearRegression()
            model.fit(X, y)

            # Get the latest data point for prediction
            latest_data = df[features].iloc[-1:].values
            print(f"Latest data shape for {symbol}: {latest_data.shape}")

            # Make prediction
            predicted_return = model.predict(latest_data)[0]

            # Blend with simple prediction for robustness
            blended_return = (predicted_return + recent_return) / 2

            # Calculate confidence based on the strength of the signal
            confidence = min(0.5 + abs(blended_return) * 5, 0.9)

            # Calculate target price
            target_price = current_price * (1 + blended_return)

            print(
                f"Prediction for {symbol}: return={blended_return:.4f}, target=${target_price:.2f}, confidence={confidence:.2f}")

            return blended_return, target_price, confidence

        except Exception as e:
            print(f"Error in prediction for {symbol}: {str(e)}")
            if 'close' in df.columns and len(df) > 0:
                current_price = df['close'].iloc[-1]
                target_price = current_price * (1 + (recent_return if 'recent_return' in locals() else 0))
                return (recent_return if 'recent_return' in locals() else 0), target_price, 0.5
            else:
                return 0, 0, 0.5


    # def _predict_return(self, symbol, df, days=30):
    #     if len(df) < 30:
    #         return 0, 0, 0
    #
    #     # # Check if required features exist
    #     # required_features = ['sma_5', 'sma_20', 'rsi_14', 'return_1d', 'return_5d', 'volatility']
    #     # for feature in required_features:
    #     #     if feature not in df.columns:
    #     #         print(f"Missing feature: {feature}")
    #     #         current_price = df['close'].iloc[-1] if 'close' in df.columns and len(df) > 0 else 0
    #     #         return 0, current_price, 0.5
    #
    #     #Calculating predicted return based on recent momentum and trend
    #     recent_return = df['return_5d'].mean() * (days / 5)
    #
    #     # Making sure df has enough data before trying to access elements
    #     if len(df) > 60:
    #         df['target'] = df['close'].shift(-30) / df['close'] - 1
    #
    #         #Features
    #         features = ['sma_5', 'sma_20', 'rsi_14', 'return_1d', 'return_5d', 'volatility']
    #
    #         train_end = max(0, len(df) - 30)
    #
    #         if train_end <= 0:
    #             # Not enough data for training, use simple prediction
    #             current_price = df['close'].iloc[-1]
    #             target_price = current_price * (1 + recent_return)
    #             return recent_return, target_price, 0.5
    #
    #
    #          #Preparing training Data
    #         try:
    #             X = df[features].iloc[:train_end]
    #             y = df['target'].iloc[:train_end]
    #
    #             #Fitting Model
    #             model = LinearRegression()
    #             model.fit(X, y)
    #
    #             #predicting data for the latest days
    #             if len(df[features]) > 0:
    #                 latest_data = df[features].iloc[-1:].values
    #                 predicted_return = model.predict(latest_data)[0]
    #
    #                 #Blending with simple prediction for robustness
    #                 predicted_return = (predicted_return + recent_return) / 2
    #
    #                 #Calculate confidence
    #                 confidence = min(0.5 + abs(predicted_return) * 5, 0.9) #Higher for stronger signals
    #
    #                 #Current price and target price
    #                 current_price = df['close'].iloc[-1]
    #                 target_price = current_price * (1 + predicted_return)
    #
    #                 return predicted_return, target_price, confidence
    #             else:
    #                 #If No data for prediction
    #                 return recent_return, df['close'].iloc[-1] * (1 + recent_return), 0.5
    #         except Exception as e:
    #             print(f"Error in ML prediction for {symbol}: {str(e)}")
    #             # Fall back to simple prediction
    #             current_price = df['close'].iloc[-1]
    #             target_price = current_price * (1 + recent_return)
    #             return recent_return, target_price, 0.5
    #
    #     #Simple model Fallback
    #     current_price = df['close'].iloc[-1]
    #     target_price = current_price * (1 + recent_return)
    #     confidence = 0.5 #Medium confidence
    #
    #     return recent_return, target_price, confidence
