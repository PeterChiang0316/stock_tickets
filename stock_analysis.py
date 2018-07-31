import pandas as pd
import seaborn as sns
import matplotlib

df = pd.read_csv('train_data.txt')

df['win_ratio'] = df.win/(df.win+df.lose)
df['buy_speed'] = df.number/df.second
df['test'] = (df.main_ratio*df.inout_ratio)**0.5
print df

sns.relplot(x="test", y="win_ratio", hue='inout_ratio', col='stock', data=df)

matplotlib.pyplot.show()