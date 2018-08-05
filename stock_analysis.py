import pandas as pd
import seaborn as sns
import matplotlib

df = pd.read_csv('train_data_last5.csv')

df['win_ratio'] = df.win/(df.win+df.lose)
df['buy_speed'] = df.number/df.second
df['test'] = (df.main_ratio*df.inout_ratio)**0.5
print df

sns.lmplot(x="test", y="win_ratio", hue='inout_ratio', data=df)

matplotlib.pyplot.show()