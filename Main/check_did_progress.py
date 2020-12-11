import os

base_folder = '/projects/b1048/gillanes/Mergers/All'
folders = os.listdir(base_folder)
n_folders = len(os.listdir(base_folder))
n_upc_did = 0
n_brand_did = 0
month_or_quarter = 'month'
for folder in folders:
	merger_folder = base_folder + '/' + folder + '/output'
	print(merger_folder)
	# print(merger_folder)
	if (os.path.exists(merger_folder + '/did_' + month_or_quarter + '.csv') or os.path.exists(merger_folder + "/did_stata_" + month_or_quarter + '_' + '0' + ".csv")):
		n_upc_did += 1
		print('upc did completed')
	if (os.path.exists(merger_folder + '/did_' + month_or_quarter + '.csv') or os.path.exists(merger_folder + "/did_stata_" + month_or_quarter + '_' + '0' + ".csv")) and os.path.exists(merger_folder + "/brandlevel_did_stata_" + month_or_quarter + '_' + '0' + ".csv"):
		n_brand_did += 1
		print('brand did completed')

print(n_upc_did)
print(n_brand_did)