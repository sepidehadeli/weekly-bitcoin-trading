import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# دانلود داده‌های بیت‌کوین از Yahoo Finance
btc_data = yf.download("BTC-USD", start="2015-01-01", end="2022-12-31")

# حذف timezone
btc_data.index = pd.to_datetime(btc_data.index).tz_localize(None)

# اضافه کردن ستون روز هفته (0: دوشنبه، 6: یکشنبه)
btc_data['Weekday'] = btc_data.index.weekday

# انتخاب روزهای یکشنبه (6) و چهارشنبه (2)
sundays = btc_data[btc_data['Weekday'] == 6].copy()
wednesdays = btc_data[btc_data['Weekday'] == 2].copy()

# اضافه کردن ستون تاریخ
sundays['Date'] = sundays.index
wednesdays['Date'] = wednesdays.index

# ریست کردن اندیس بدون اضافه کردن مجدد ستون تاریخ
sundays.reset_index(inplace=True, drop=True)
wednesdays.reset_index(inplace=True, drop=True)

# ادغام داده‌های یکشنبه و چهارشنبه
merged_df = pd.merge_asof(
    sundays, wednesdays, on='Date', direction='forward', suffixes=('_sunday', '_wednesday')
)

# حذف سطرهایی که مقادیر NaN دارند
merged_df.dropna(inplace=True)

# جایگزینی مقادیر بسیار کوچک Open_sunday با صفر
merged_df['Open_sunday'] = merged_df['Open_sunday'].map(lambda x: 0 if abs(x) < 1e-6 else x)

# بررسی تعداد مقادیر صفر در ستون Open_sunday
print(f"Number of zero values in Open_sunday: {(merged_df['Open_sunday'] == 0).sum()}")

# جایگزینی مقادیر صفر در Open_sunday با یک مقدار کوچک
merged_df['Open_sunday'] = merged_df['Open_sunday'].replace(0, 1e-6)

# سرمایه اولیه
initial_capital = 1000

# محاسبه مقدار بیت‌کوین خریداری شده در هر یکشنبه
merged_df['btc_owned'] = initial_capital / merged_df['Open_sunday']

# محاسبه سرمایه در هر چهارشنبه (با فرض فروش تمام بیت‌کوین)
merged_df['capital'] = merged_df['btc_owned'].squeeze() * merged_df['Close_wednesday'].squeeze()

# اضافه کردن ستون سرمایه اولیه یکشنبه
merged_df['capital_sunday'] = initial_capital

# تبدیل نوع داده ستون capital_sunday به float
merged_df['capital_sunday'] = merged_df['capital_sunday'].astype(float)

# به‌روزرسانی سرمایه هر یکشنبه بر اساس سرمایه چهارشنبه قبلی با استفاده از loc
for i in range(1, len(merged_df)):
    merged_df.loc[i, 'capital_sunday'] = merged_df.loc[i-1, 'capital']

# محاسبه مقدار بیت‌کوین خریداری‌شده
merged_df['btc_owned'] = merged_df['capital_sunday'].squeeze() / merged_df['Open_sunday'].squeeze()

# محاسبه سرمایه در هر چهارشنبه (با فرض فروش تمام بیت‌کوین)
merged_df['capital'] = merged_df['btc_owned'].squeeze() * merged_df['Close_wednesday'].squeeze()

# محاسبه سود در هر معامله
merged_df['profit'] = merged_df['capital'] - merged_df['capital_sunday']

# محاسبه سود تجمعی
merged_df['cumulative_profit'] = merged_df['profit'].cumsum()

# محاسبه سرمایه نهایی و سود کل
final_capital = merged_df['capital'].iloc[-1]
total_profit = final_capital - initial_capital

# چاپ نتایج
print(f"Initial Capital: ${initial_capital:.2f}")
print(f"Final Capital: ${final_capital:.2f}")
print(f"Total Profit: ${total_profit:.2f}")

# رسم نمودار سود تجمعی
plt.figure(figsize=(12, 6))
plt.plot(merged_df['Date'], merged_df['cumulative_profit'], label='Cumulative Profit Over Time', color='blue', marker='o')
plt.title(f'Bitcoin Investment Performance (Buy on Sunday, Sell on Wednesday)')
plt.xlabel(f'Date')
plt.ylabel(f'Cumulative Profit (USD)')
plt.grid(True)
plt.legend()
plt.tight_layout()

# نمایش نمودار
plt.show()

merged_df.to_csv('merged_data.csv', index=False)