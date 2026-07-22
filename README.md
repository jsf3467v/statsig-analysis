# Experiment Analysis Toolkit

[![CI](https://github.com/jsf3467v/statsig-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/jsf3467v/statsig-analysis/actions/workflows/ci.yml)

A statistics engine for online controlled experiments, with a pluggable
assignment-and-logging backend. It reads variant assignments, exposures, and
events, and scores outcomes with vectorized statistics and confidence intervals.
The engine implements the two-proportion test, Welch's t-test, sequential
probability ratio testing, winsorization, power and sample-size planning, and
variance reduction via CUPED (Controlled-experiment Using Pre-Experiment Data).
Every test is verified against a reference implementation. A
[Statsig](https://statsig.com) SDK integration is included as a reference
backend and runs fully offline, connecting to a live project once a single
environment variable is set.


## Objective

The toolkit reads variant assignment and records exposures and events through
the Statsig integration in `src/experiment/sdk.py`, which wraps the standard
calls of checking a gate, reading an experiment, and logging an event with
automatic exposure logging. It scores an experiment through a shared result
type so that every metric is comparable, and it renders a plain summary of the
outcome through `report.py`. The statistical work lives in
`src/experiment/stats.py`.

## Starting Project

```bash
pip install -r requirements.txt          # numpy, scipy
PYTHONPATH=src python -m experiment simulate                       # build a dataset (save point)
PYTHONPATH=src python -m experiment analyze data/experiment.csv    # score it
PYTHONPATH=src python -m experiment size --base 0.10 --mde 0.012   # sample size per arm
```

The example run below uses synthetic data with a known conversion lift of
$0.012$.

```
- conversion_diff: +0.0148 [+0.0087, +0.0208], p = 0.0000 (significant)
- mean_diff (revenue):        +0.4724 [+0.2721, +0.6727], p = 0.0000
- mean_diff (revenue, CUPED): +0.4758 [+0.3986, +0.5530], p = 0.0000
```

CUPED holds the point estimate steady while it reduces the width of the interval
by roughly $2.5\times$, which is the variance reduction an experimentation
platform depends on.

## Data

The dataset is synthetic. The `experiment simulate` command generates it with a
seeded random number generator and a planted effect, so it holds no real user
information and exists only so the analysis can be checked against a known
ground truth.

## Statsig Integration

```bash
pip install -r requirements-sdk.txt      # statsig-python-core
PYTHONPATH=src python -m experiment sdk-demo
```

The demonstration runs fully offline through `disable_network` and local
overrides, so it executes without a Statsig account. To run against a live
project, provide a server key through the environment.

```bash
export STATSIG_SERVER_SECRET=secret-...
```

## Methods

The two-proportion test measures the difference in conversion rate between
treatment and control. It computes the $p$ value from the pooled standard error,
which is the correct choice under the null hypothesis of equal rates, and it
computes the confidence interval from the unpooled standard error, which is the
correct interval for a difference of proportions. An arm with zero units raises
an error rather than divide by zero.

The Welch test compares a continuous metric across the two arms without assuming
equal variance, using the Welch and Satterthwaite degrees of freedom. Its result
is verified against `scipy.stats.ttest_ind`.

Sequential testing follows the method of Wald. The log likelihood ratio of the
data under the alternative rate $p_1$ against the null rate $p_0$ is compared
with the two boundaries $\log\!\left(\frac{1-\beta}{\alpha}\right)$ and
$\log\!\left(\frac{\beta}{1-\alpha}\right)$, and the outcome is to reject, to
accept, or to continue. This allows an experiment to stop early without
inflating the false-positive rate the way repeated fixed-horizon testing would.

Winsorization clips both tails of a metric at a chosen quantile, which limits
the influence of outliers on a mean and suits a heavy-tailed revenue metric.

The power and sample size use the normal approximation for a two-proportion test.
The `sample_size` function returns the units per arm needed for a target power
and a minimum detectable effect, and the `power` function returns the power
achieved at a given sample size. The two are mutually consistent, so that
$\text{power}(\text{base}, \text{mde}, \text{sample\_size}(\text{base}, \text{mde}))$
recovers the target.

CUPED reduces variance using a pre-experiment covariate. With covariate $X$ and
metric $Y$, the adjustment coefficient is
$\theta = \operatorname{cov}(Y, X) / \operatorname{var}(X)$ and the adjusted
metric is $Y - \theta\,(X - \bar{X})$. Because the adjustment has zero mean, the
estimate of the treatment effect is unchanged, while the variance falls in
proportion to the strength of the correlation between the covariate and the
metric.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
ruff check .
```

The statistics are checked for correctness rather than coverage alone. The Welch
test is verified against `scipy.stats.ttest_ind`, the two-proportion test
against a hand computation, the sample size against the power function, and
CUPED against the requirement that variance falls while the mean is preserved.
The continuous integration workflow on GitHub runs the linter and the tests on
every push.

## References

1. Deng, A., Xu, Y., Kohavi, R., and Walker, T. (2013). Improving the Sensitivity of Online Controlled 
Experiments by Utilizing Pre-Experiment Data. Proceedings of the Sixth ACM International Conference on 
Web Search and Data Mining (WSDM 2013). https://doi.org/10.1145/2433396.2433413


2. Wald, A. (1945). Sequential Tests of Statistical Hypotheses. The Annals of Mathematical Statistics, 16(2), 
117–186. https://doi.org/10.1214/aoms/1177731118

## License

MIT. See LICENSE.
