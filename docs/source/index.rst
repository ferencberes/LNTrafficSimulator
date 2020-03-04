Welcome to lnsimulator's documentation!
=======================================

This Python package was designed to empirically study the transaction fees and privacy provisions of Bitcoin's Lightning Network (LN). The simulator relies only on the publicly available data of network structure and capacities, and generates transactions under assumptions that we validated based on information spread by blog posts of LN node owners.

What's in it for me?
====================

We think that our simulator can be of interest mainly for two types of people: LN node owners and researchers. Hence, the simulator can answer the following questions of interest for these people:

i.) LN node owners, routers:
----------------------------

*    What is the optimal fee I could charge for transactions going through my node in order to maximise my routing profits?
*    What is my expected income from routing with respect to certain parameters (topology, traffic, transacted amounts)?
*    How various parameters (topology, traffic, transacted amounts) affect the profitability of my nodes?

ii.) Researchers:
-----------------

*    What is the optimal fee nodes can charge? How far is it (if at all) from on-chain fees?
*    What is the path length distribution of transactions on the LN graph? How much anonymity do they provide?
*    How profitable is it to run a router node? Who are the most profitable ones?
*    Is everyone altruistic on the LN transaction fee market?
*    How various parameters (topology, traffic, transacted amounts) affect the profitability of each node?

Our research paper **"A Cryptoeconomic Traffic Analysis of Bitcoin's Lightning Network"** is available on `arXiv <https://arxiv.org/abs/1911.09432>`_.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   simulator_docs
   advanced_docs
   acknowledgements
