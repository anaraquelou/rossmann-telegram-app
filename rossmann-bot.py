import config
import os
import requests
import json
import pandas as pd
import numpy as np

from flask import Flask, request, Response

# info about the bot
# https://api.telegram.org/bot5925337760:AAFltUssi8Tbkz8hxzfA2yha_J_33xV_bJ8/getMe

# get updates
# https://api.telegram.org/bot5925337760:AAFltUssi8Tbkz8hxzfA2yha_J_33xV_bJ8/getUpdates

# Webhook
# https://api.telegram.org/bot5925337760:AAFltUssi8Tbkz8hxzfA2yha_J_33xV_bJ8/setWebhook?url=https://49dd8047158d9a.lhr.life/

# Webhook Render
# https://api.telegram.org/bot5925337760:AAFltUssi8Tbkz8hxzfA2yha_J_33xV_bJ8/setWebhook?url=https://rossmann-telegram-app-39zc.onrender.com

# send message
# https://api.telegram.org/bot5925337760:AAFltUssi8Tbkz8hxzfA2yha_J_33xV_bJ8/sendMessage?chat_id=5854880522&text=Oi%20Raquel

def send_message( chat_id, text ):
	url ='https://api.telegram.org/bot{}/'.format( config.token )
	url = url + 'sendMessage?chat_id={}'.format( chat_id )
	
	r = requests.post( url, json={'text': text} )
	print( 'Status code {}'.format( r.status_code ) )
	
	return None


def load_dataset( store_id ):
	# loading test dataset
	df10 = pd.read_csv( 'test.csv' )
	df_store_raw = pd.read_csv( 'store.csv' )

	# merge test and store dataset
	df_test = pd.merge( df10, df_store_raw, how = 'left', on = 'Store'  )

	# chose store for prediction
	
	df_test = df_test[df_test['Store'] == store_id ]
	
	if not df_test.empty:

		# remove days store is closed
		df_test = df_test[ df_test['Open'] != 0 ]
		df_test = df_test[ ~df_test['Open'].isnull() ]
		df_test = df_test.drop( 'Id', axis=1 )

		# convert dataframe to json
		data = json.dumps( df_test.to_dict( orient = 'records' ) )
	
	else:
		data = 'error'
	
	return data
	
def predict( data ):
	# API call
	url = 'https://rossmann-sales-x79b.onrender.com/rossmann/predict'
	header = { 'Content-type': 'application/json' }
	data = data

	r = requests.post( url, data = data, headers = header )
	print( 'Status code: {} '.format(r.status_code) )

	d1 = pd.DataFrame( r.json(), columns = r.json()[0].keys() )
	
	return d1
	

def parse_message( message ):
	chat_id = message['message']['chat']['id']
	store_id = message['message']['text']
	
	store_id = store_id.replace( '/', '' )
	
	try:
		store_id = int( store_id )
	except ValueError:
		store_id = 'error'
	
	return chat_id, store_id


# API initialize
app = Flask( __name__ )

@app.route( '/', methods = [ 'GET', 'POST' ] )
def index():
	if request.method == 'POST':
		message = request.get_json()
		
		chat_id, store_id = parse_message( message )
		
		if store_id != 'error':
			# loading data
			data = load_dataset( store_id )
			if data != 'error':
				# prediction
				d1 = predict( data )
				# calculation
				d2 = d1[ ['store', 'prediction'] ].groupby( 'store' ).sum().reset_index()
				# send message
				msg = 'Loja nº {} vai vender R$ {:,.2f} nas pŕoximas seis semanas.'.format( 
				d2['store'].values[0], 
				d2['prediction'].values[0] )
				
				send_message( chat_id, msg )
				return Response( 'Ok', status=200 )
				
			else:
				send_message( chat_id, 'Loja nº {} não disponível.'.format(store_id) )
				return Response( 'Ok', status=200 )
		else:
			send_message( chat_id, 'Erro: não é um número de loja.' )
			return Response( 'OK', status=200 )
			
	else:
		return '<h1> Rossmann Telegram BOT </h1>'
	
		
if __name__ == '__main__':
	port = os.environ.get( 'PORT', 5000 )
	app.run( host = '0.0.0.0', port=port )
