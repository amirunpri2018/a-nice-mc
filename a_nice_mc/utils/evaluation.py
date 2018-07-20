import numpy as np


def auto_correlation_time(x, s, mu, var):
    b, t, d = x.shape
    act_ = np.zeros([d])
    for i in range(0, b):
        y = x[i] - mu
        p, n = y[:-s], y[s:]
        act_ += np.mean(p * n, axis=0) / var
    act_ = act_ / b
    return act_


def effective_sample_size(x, mu, var, logger):
    """
    Calculate the effective sample size of sequence generated by MCMC.
    :param x:
    :param mu: mean of the variable
    :param var: variance of the variable
    :param logger: logg
    :return: effective sample size of the sequence
    Make sure that `mu` and `var` are correct!
    """
    # batch size, time, dimension
    b, t, d = x.shape
    ess_ = np.ones([d])
    for s in range(1, t):
        p = auto_correlation_time(x, s, mu, var)
        if np.sum(p > 0.05) == 0:
            break
        else:
            for j in range(0, d):
                if p[j] > 0.05:
                    ess_[j] += 2.0 * p[j] * (1.0 - float(s) / t)

    logger.info('ESS: max [%f] min [%f] / [%d]' % (t / np.min(ess_), t / np.max(ess_), t))
    return t / ess_

def batch_effective_sample_size(x, mu, var, logger=None):
    """
    Calculate the effective sample size of sequence generated by MCMC.
    :param x:
    :param mu: mean of the variable
    :param var: variance of the variable
    :param logger: log
    :return: effective sample size of the sequence

    We calculate the effective sample size using the method of batch
    means, which compares the variance of the chain to the variance of means of
    chuncks of the chain. This obviates the need to know the true mean and
    variance of the distribution as is required for other estimators.
    """


    M, T, D = x.shape
    x = np.transpose(x, [1, 0, 2])
    num_batches = int(np.floor(T ** (1 / 3)))
    batch_size = int(np.floor(num_batches ** 2))
    print('batch_size', batch_size)
    print('num_batches', num_batches)
    batch_means = []
    for i in range(num_batches):
        batch = x[batch_size * i:batch_size * i + batch_size]
        batch_means.append(np.mean(batch, axis=0))
    batch_variance = np.var(np.stack(batch_means), axis=0)
    chain_variance = np.var(x, axis=0)

    ess = chain_variance / (batch_variance * batch_size)

    if logger:
        logger.info(
            'ESS: min [%f] max [%f] / [%d]' % (np.min(ess), np.max(ess), 1))

    return ess


def acceptance_rate(z):
    cnt = z.shape[0] * z.shape[1]
    for i in range(0, z.shape[0]):
        for j in range(1, z.shape[1]):
            if np.min(np.equal(z[i, j - 1], z[i, j])):
                cnt -= 1
    return cnt / float(z.shape[0] * z.shape[1])


def gelman_rubin_diagnostic(x, logger, mu=None):
    m, n = x.shape[0], x.shape[1]
    theta = np.mean(x, axis=1)
    sigma = np.var(x, axis=1)
    # theta_m = np.mean(theta, axis=0)
    theta_m = mu if mu is not None else np.mean(theta, axis=0)
    b = float(n) / float(m-1) * np.sum((theta - theta_m) ** 2)
    w = 1. / float(m) * np.sum(sigma, axis=0)
    v = float(n-1) / float(n) * w + float(m+1) / float(m * n) * b
    r_hat = np.sqrt(v / w)
    logger.info('R: max [%f] min [%f]' % (np.max(r_hat), np.min(r_hat)))
    return r_hat
