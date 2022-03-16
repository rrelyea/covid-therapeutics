# Ways to view current Evusheld order/inventory data for all 50 states

- Use https://rrelyea.github.io/evusheld

  - or view same data in [a searchable map (HHS)](https://covid-19-therapeutics-locator-dhhs.hub.arcgis.com/), [Microsoft Excel](https://1drv.ms/x/s!AhC1RgsYG5Ltv55eBLmCP2tJomHPFQ?e=XbsTzD), [Google Sheets](https://docs.google.com/spreadsheets/d/14jiaYK5wzTWQ6o_dZogQjoOMWZopamrfAlWLBKWocLs/edit?usp=sharing), [CSV File](https://raw.githubusercontent.com/rrelyea/evusheld-locations-history/main/evusheld-data.csv), or [HealthData.gov](https://healthdata.gov/Health/COVID-19-Public-Therapeutic-Locator/rxn6-qnx8/data)
  
# Where does this data comes from?
HealthData.gov collects all medical facilities with Evusheld orders/inventory and publishes it to https://healthdata.gov/Health/COVID-19-Public-Therapeutic-Locator/rxn6-qnx8

Every 20 minutes, this site:
- check for a newer version of https://healthdata.gov/resource/rxn6-qnx8.csv?order_label=Evusheld
- sorts it by state, county, city, providerName
- saves it as [evusheld-data.csv](https://github.com/rrelyea/evusheld-locations-history/blob/main/evusheld-data.csv)

HealthData.gov has been updating the data feed about 1 time per weekday)

# How can we improve Evusheld dose flow to people who need it?
- Read this set of suggestions...and send me ideas, or edit (wiki): [evusheld-requests](https://github.com/rrelyea/evusheld-locations-history/wiki/Evusheld-Requests)

# Contact info for your state's health department
- [state-health-departments.csv](https://github.com/rrelyea/evusheld-locations-history/blob/main/state-health-departments.csv) has web page and twitter accounts for most state health departments.
  - open an issue, PR, or contact me with improvements.

# Contact/Feedback
- Open an issue or pull request in this repository
- or contact Rob Relyea at [@rrelyea](https://twitter.com/rrelyea) on twitter
