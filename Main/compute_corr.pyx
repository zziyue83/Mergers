import time
import numpy as np

def get_den(u):
    n = len(u)
    z = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if i > j:
                z[i, j] = z[j, i]
            else:
                z[i, j] = np.sqrt(u[i]*u[j])
                
    return z

def corr(df):
    start = time.process_time()
    
    df = df.fillna(0)
    x_mean = np.mean(df,axis=0)
    r_num = np.transpose(df-x_mean).dot(df-x_mean)
    r_den = get_den(np.sum((df-x_mean)**2,axis=0))
    r = r_num/r_den

    process_time = time.process_time() - start
    print(process_time)

    return r