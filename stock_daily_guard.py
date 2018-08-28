import stock_ticket
from tools.stock_price_utility import Stock
import pandas as pd
import bisect
import numpy as np
import random
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC


def main():
    stock_list = ['2454', '2439', '2455', '2448', '2377', '3035',
                  '2456', '2313', '5269', '2383', '1312', '2353', '1707',
                  '3443', '4906']
    stock_list += ['2915', '5264', '2311', '2105', '3673', '2542', '3044', '2610', '6116', '1319', '2059', '2356']
    stock_list += ['3017', '2485', '1536', '3376', '2603', '6285', '3665', '1476']
    df = pd.DataFrame(columns=(
        's', 'date', 'last_date', 'K9', 'D9', 'BIAS5', 'BIAS10', 'RSI10', 'RSI5', 'DIF_MACD', 'MA5', 'STD5', 'MA10',
        'STD10', 'last_date_close', 'BOOL_HIT'))
    for s in stock_list:
        ship = Stock(s)

        win_standard_dict = {}
        sim_start_date = '20180525'
        sim_end_date = '20180815'


        finance = ship.get_stock_finance()

        for date in ship.iterate_date(sim_start_date, sim_end_date):

            print '[%s] Date: %s' % (s, date)
            info = ship.get_daily_info(date, every_transaction=True)

            transaction = info.data

            if not transaction:
                continue

            win_standards = stock_ticket.stock_win_point_test(s, date, transaction, minutes=5)

            left = bisect.bisect_left(finance.keys(), date)
            last_date = finance.keys()[left - 1]
            last_finance = finance.values()[left - 1]
            print last_finance

            last5 = map(lambda v: v['ClosePr'], finance.values()[left - 6:left - 1])
            std5 = np.std(last5, ddof=1)
            bias5 = 100 * (last_finance['ClosePr'] - sum(last5) / 5) / last_finance['ClosePr']

            last10 = map(lambda v: v['ClosePr'], finance.values()[left - 11:left - 1])
            std10 = np.std(last10, ddof=1)
            bias10 = 100 * (last_finance['ClosePr'] - sum(last10) / 10) / last_finance['ClosePr']

            df = df.append(
                pd.Series({'s': s, 'date': date, 'last_date': last_date, 'last_date_close': last_finance['ClosePr'],
                           'K9': last_finance['K9'], 'D9': last_finance['D9'], 'BIAS5': bias5, 'BIAS10': bias10,
                           'RSI10': last_finance['RSI10'], 'RSI5': last_finance['RSI5'],
                           'DIF_MACD': last_finance['DIF_MACD'],
                           'STD5': std5, 'MA5': sum(last5) / 5, 'STD10': std10, 'MA10': sum(last10) / 10,
                           'BOOL_HIT': 1 if len(win_standards) else 0}), ignore_index=True)

    df.to_csv('2456_report.csv')


def accuracy(golden, test):
    total_success = sum(golden)
    success_count, miss_count = 0.0, 0.0

    for g, t in zip(golden, test):
        if g == 1 and t == 1:
            success_count += 1
        if g == 0 and t == 1:
            miss_count += 1

    print 'total count %d' % len(golden)
    print 'success percentage %f' % (success_count/total_success)
    print 'success_count %d/ miss_count %d' % (success_count, miss_count)

if __name__ == '__main__':
    #main()
    #exit(0)
    df = pd.read_csv('2456_report.csv')
    #df['STD5'] = #df['STD5']/df['MA5']
    #df['STD10'] = 100*df['STD10']/df['MA10']
    df['DIF_MACD'] = (df['DIF_MACD']-df['DIF_MACD'].min())/(df['DIF_MACD'].max()-df['DIF_MACD'].min())
    df['BIAS5'] = (df['BIAS5']-df['BIAS5'].min())/(df['BIAS5'].max()-df['BIAS5'].min())
    df['BIAS10'] = (df['BIAS10']-df['BIAS10'].min())/(df['BIAS10'].max()-df['BIAS10'].min())
    df['RSI5'] = df['RSI5'] / 100
    df['RSI10'] = df['RSI10']/100
    df['K9'] = df['K9']/100
    df['D9'] = df['D9']/100


    for s in df['s'].unique():
        total = sum(df.loc[df['s'] == s]['BOOL_HIT'])
        print s, total
        if total < 3:
            df = df[df.s != s]

    print df['s'].unique()

    feature_names = ['K9', 'D9', 'DIF_MACD', 'BIAS5', 'BIAS10', 'RSI5', 'RSI10']
    X = df[feature_names]
    y = df['BOOL_HIT']

    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=1)
    print len(y_train.values)

    X_train['BOOL_HIT'] = y_train.values

    hit_data = X_train.loc[X_train['BOOL_HIT'] > 0].reset_index(drop=True)
    hit = len(hit_data)
    data_count_diff = len(X_train['BOOL_HIT']) - hit
    for _ in range(data_count_diff):
        X_train = X_train.append(hit_data.iloc[random.randint(0, hit-1), :], ignore_index=True)

    y_train = X_train['BOOL_HIT']
    X_train = X_train[feature_names]


    print len(y_train), hit
    print type(y_test), type(X_test)

    logreg = LogisticRegression()
    logreg.fit(X_train, y_train)
    accuracy(y_test.values, logreg.predict(X_test))

    print('Accuracy of Logistic regression classifier on training set: {:.2f}'
          .format(logreg.score(X_train, y_train)))
    print('Accuracy of Logistic regression classifier on test set: {:.2f}'
          .format(logreg.score(X_test, y_test)))

    clf = DecisionTreeClassifier().fit(X_train, y_train)
    print('Accuracy of Decision Tree classifier on training set: {:.2f}'
          .format(clf.score(X_train, y_train)))

    accuracy(y_test.values, clf.predict(X_test))

    print('Accuracy of Decision Tree classifier on test set: {:.2f}'
          .format(clf.score(X_test, y_test)))

    knn = KNeighborsClassifier()
    knn.fit(X_train, y_train)
    accuracy(y_test.values, knn.predict(X_test))
    print('Accuracy of K-NN classifier on training set: {:.2f}'
          .format(knn.score(X_train, y_train)))
    print('Accuracy of K-NN classifier on test set: {:.2f}'
          .format(knn.score(X_test, y_test)))

    svm = SVC()
    svm.fit(X_train, y_train)
    accuracy(y_test.values, svm.predict(X_test))
    print svm.predict(X_test)
    print('Accuracy of SVM classifier on training set: {:.2f}'
          .format(svm.score(X_train, y_train)))
    print('Accuracy of SVM classifier on test set: {:.2f}'
          .format(svm.score(X_test, y_test)))

    #sns.relplot(x='K9#', y='BOOL_HIT', hue='STD5',data=df)
    #plt.show()

