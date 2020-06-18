import sys

code = sys.argv[1]
log_out = open('../../../All/m_' + code + '/output/select_products.log', 'w')
sys.stdout = log_out
print("you are running the merger with code: "+code)