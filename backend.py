from flask import Flask, render_template, request, send_file
from geopy.geocoders import ArcGIS
from werkzeug import secure_filename
import folium
import pandas as pd
import numpy as np
import datetime

app = Flask(__name__)
file_name = None

def get_geocodes(df):
    gis = ArcGIS(timeout=10)
    lon = []; lat = [];
    for indx, address in df['Address'].iteritems():
        gcode = gis.geocode(address)
        if gcode:
            lon.append(gcode.longitude)
            lat.append(gcode.latitude)
        else:
            lon.append(None)
            lat.append(None)
    df['Latitude'] = lat
    df['Longitude'] = lon

    return df

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/success', methods=['POSt'])
def success():
    global file_name
    if request.method == 'POST':
        up_file = request.files['address_file']
        if up_file:
            file_name = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f.csv')
            try:
                dataset = pd.read_csv(up_file)
                if 'address' in dataset.columns or 'Address' in dataset.columns:
                    dataset.columns = ['Address' if column == 'address' else column for column in dataset.columns]
                    dataset = get_geocodes(dataset)
                    dataset.to_csv(f"uploads/{file_name}")
                    return render_template("index.html", success_data=dataset.to_html(),
                                            btn="download.html",
                                            file_name=f'GeoCodes of addresses in File: <strong>{file_name}</strong>')
            except:
                pass
    return render_template("index.html", err_data="Please enter a valid CSV file that contains an Address column!!")

@app.route('/download')
def download():
    return send_file(f"uploads/{file_name}", as_attachment=True, mimetype='text/csv', attachment_filename='Download.csv')

@app.route('/plot')
def plot():
    map = folium.Map(location=[28.00, 77.00], zoom_start=8, tiles='Stamen Terrain')
    fg = folium.FeatureGroup(name="Address Layer")
    df = pd.read_csv(f"uploads/{file_name}")
    popup_info =  """<h4>Address Information:</h4>
                    Name: {}<br>
                    Address: {}                
                  """

    for i, row in df.iterrows():
        iframe = folium.IFrame(html=popup_info.format(row['Name'], row['Address']), width=200, height=100)
        if not np.isnan(row['Latitude']):
            fg.add_child(folium.Marker(radius=7,
                                        location=[row['Latitude'], row['Longitude']],
                                        popup=folium.Popup(iframe),
                                        fill = True,
                                        fill_color='green',
                                        color='grey',
                                        fill_opacity=0.8
                                        )
                        )
    map.add_child(fg)
    map.add_child(folium.LayerControl())
    return map.get_root().render()

if __name__ == "__main__":
    app.run(debug=True)
