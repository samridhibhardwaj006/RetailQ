# Data card

**Dataset:** UCI Online Retail (Chen, 2015), DOI 10.24432/C5BW33  
**License:** CC BY 4.0  
**Coverage:** 1 Dec 2010 to 9 Dec 2011  
**Publisher description:** transactions from a UK-based registered non-store retailer selling all-occasion giftware. The retailer is anonymised in the published data.

## Intended use
Educational analytics, portfolio demonstrations, customer segmentation, descriptive analysis and reproducible experimentation.

## Not intended for
Current market sizing, live operational decisions, identifying the retailer, re-identifying customers, or making automated decisions about real individuals.

## Processing
The application parses dates, numeric quantity/price, computes line revenue and identifies return/cancellation records. Positive sales are analysed separately from return/cancellation lines. Customer-level models omit rows with missing CustomerID.

## Known limitations
Historical period; anonymised business; missing customer identifiers; possible data entry anomalies; customer segment labels are heuristic; forecasting is a simple trend baseline.
