from astroquery.vizier import Vizier
vizier = Vizier()
catalog_list = vizier.find_catalogs('UKIDSS')
for i, j in catalog_list.items():
    print(i, ":", j.description)





