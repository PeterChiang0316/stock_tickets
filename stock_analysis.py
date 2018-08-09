import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_csv('train_data.csv')

df['win_ratio'] = df.win/(df.win+df.lose)
df['buy_speed'] = df.number/df.second

sns.relplot(x="main_ratio", y="win_ratio", hue='inout_ratio', data=df)

plt.xlim(0, None)
plt.ylim(0, None)

plt.show()