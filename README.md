# MSc Coursework Examples

## Description

These are a few of the more substantive projects completed as part of my DS MSc program (2021-2023).

## Contents

+ **Multi-label Classification of Products**

> *Given a set of product descriptions and three category labels, exploratory analysis is performed to inform data cleaning steps. Customized text processing is applied to produce term-frequency inverse document-frequency vectors. These are used to train cascading series of naïve bayes classifiers to target the three levels of product category successively.*

> ***KW: Classification, Naïve Bayes, NLP, TF-IDF***

****

+ **Distributed Insights for LMS Logs Analysis**

> *Hypotheses about the significance of platform features and user demographics in relation to consistent engagement are explored in LMS logs using Pyspark sql and MLlib. Analysis relies on significant filtering and binning based on aggregations of timestamps, joins to demographic data, crosstabulation, as well as parameterized grid search with random forest classifiers and feature importance inspection by average impurity.*

> ***KW: PySpark, Feature Importance, SQL***

****

+ **Deep Neural Network Architecture Search**

> *A dataset of sentences extracted from reviews of Amazon products tagged for usefulness in purchase decision making is used to define a regression problem. An initial feed-forward model is developed to operate in a low-information environment using only syntactic token presence one-hot encoded and optimized to outperform a naïve baseline. Using learned embeddings a gradient descent regressor and a single-layer recurrent neural net are defined as baselines. A functional hypermodel is then defined that facilitates parameter tuning and comparison of multi-layer and multi-input neural nets that optionally take product titles as a second input using pre-trained embeddings. Models are tuned using a Bayesian optimizer. Model performance is subjected to a custom ranking task scored by Kendall's tau metric, simulating real-world performance and differentiating where standard regressor scoring techniques do not.*

> ***KW: Regression, Recurrent Neural Network, NLP, HP tuning***

****

+ **Parallel Proof-of-Work**

> *Implementation of blockchain mining node. Includes transaction and block verification, as well as a parallelized mining function using a stratified random nonce search. Mining is completed as part of coursework requirements on multiple platforms using between 2 and 36 processing tasks. A 51% attack is forensically analyzed and a potential mitigation strategy using anomaly detection in nonce search strategy is suggested. Note: Because this assignment works to a tight spec, only parallel mining code and blockchain analysis are included.*

> ***KW: Blockchain, Multiprocessing, Cryptography***

****

## License

[AGPL-3.0-only](https://choosealicense.com/licenses/agpl-3.0/#)