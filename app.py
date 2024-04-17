from flask import Flask, render_template, request, jsonify, redirect, url_for, flash,session
import mysql.connector, re

app = Flask(__name__)
app.secret_key = 'your_very_secret_key'

# Database connection parameters
db_params = {
    'user': 'sql8699876',                             # Your MySQL username
    'password': 'XFIelYI5ne',                        # Your MySQL password
    'host': 'sql8.freemysqlhosting.net',             # Typically 'localhost' for a locally hosted database
    'database': 'sql8699876',   # Your actual database name
}

@app.route('/')
def home():
    # Home page with links to other views
    return render_template('home.html')

@app.route('/channels', methods=['GET'])
def get_channels():
    # Fetch all channels and their languages
    conn = mysql.connector.connect(**db_params)
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT channelName, channel_language FROM channels')  # Adjust the column names as needed
    channels = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('channelsfilteredbylanguage.html', channels=channels)

@app.route('/top-rockets', methods=['GET'])
def get_top_rockets():
    # Query the database for the top 5 rockets by number of satellites launched
    conn = mysql.connector.connect(**db_params)
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT `launching_rocket`, COUNT(*) AS `number_of_satellites`
        FROM satellite
        GROUP BY `launching_rocket`
        ORDER BY `number_of_satellites` DESC
        LIMIT 5
    ''')
    top_rockets = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('top5rockets.html', top_rockets=top_rockets)

@app.route('/top-channels-per-language', methods=['GET'])
def top_channels_per_language():
    conn = mysql.connector.connect(**db_params)
    cursor = conn.cursor(dictionary=True)
    # Ensure only channels with a defined language are considered
    cursor.execute('''
        SELECT `channelName`, `channel_language`, COUNT(*) AS `popularity`
        FROM channels
        WHERE `channel_language` IS NOT NULL AND TRIM(`channel_language`) <> ''
        GROUP BY `channel_language`, `channelName`
        ORDER BY `channel_language`, `popularity` DESC
    ''')
    raw_channels = cursor.fetchall()
    cursor.close()
    conn.close()

    # Aggregate channels by language
    channels_by_language = {}
    for channel in raw_channels:
        lang = channel['channel_language']
        if lang not in channels_by_language:
            channels_by_language[lang] = []
        if len(channels_by_language[lang]) < 5:
            channels_by_language[lang].append(channel)

    return render_template('top_channels_per_language.html', channels_by_language=channels_by_language)

@app.route('/satellites')
def all_satellites():
    regions = ['Atlantic', 'Asia', 'Europe', 'America']
    satellites_by_region = {}

    conn = mysql.connector.connect(**db_params)
    cursor = conn.cursor(dictionary=True)

    for region in regions:
        query = '''
            SELECT Satellite_name, region
            FROM satellite
            WHERE region = %s
        '''
        cursor.execute(query, (region,))
        satellites_by_region[region] = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('satellites.html', satellites_by_region=satellites_by_region)


def clean_position(raw_pos):
    """ Extracts the first occurring decimal number from a string. """
    match = re.search(r'[-+]?\d*\.\d+|\d+', raw_pos)
    return float(match.group(0)) if match else None

@app.route('/satellites/position', methods=['GET', 'POST'])
def satellites_by_position():
    if request.method == 'POST':
        position = request.form.get('position', type=float)
        if position is None:
            flash("Invalid position provided.", "error")
            return render_template('satellites_by_position.html', error="Invalid position provided.")

        # Define the position range
        position_min = position - 10
        position_max = position + 10

        # Fetch raw satellite positions
        conn = mysql.connector.connect(**db_params)
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT `Satellite_name`, `position` FROM satellite')
        raw_satellites = cursor.fetchall()
        cursor.close()
        conn.close()

        # Clean and filter satellites within the position range
        satellites = [
            {'Satellite_name': sat['Satellite_name'], 'position': sat['position']}
            for sat in raw_satellites
            if clean_position(sat['position']) is not None and position_min <= clean_position(sat['position']) <= position_max
        ]

        return render_template('satellites_by_position.html', satellites=satellites, position=position)
    else:
        # No position provided, show empty form
        return render_template('satellites_by_position.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']

        conn = mysql.connector.connect(**db_params)
        cursor = conn.cursor()

        # Check if the username or email already exists
        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            flash('Username or email already exists. Please choose another.', 'error')
            return render_template('register.html')
        
        flash('Registration successful! Welcome, {}!'.format(username), 'success')
        return redirect(url_for('home'))
    else:
        return render_template('register.html')


@app.route('/favorite-channels', methods=['GET', 'POST'])
def favorite_channels():
    conn = mysql.connector.connect(**db_params)
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Collect favorite channels from the form
        favorite_channels = request.form.getlist('favorite_channels')
        session['favorite_channels'] = favorite_channels  # Store in session for now
        flash('Favorite channels updated!', 'success')
        return redirect(url_for('favorite_channels'))

    # Fetch all channels for display
    cursor.execute('SELECT channelName FROM channels')
    channels = cursor.fetchall()
    cursor.close()
    conn.close()

    selected_favorites = session.get('favorite_channels', [])
    return render_template('favorite_channels.html', channels=channels, selected_favorites=selected_favorites)
if __name__ == '__main__':
    app.run(debug=True)



        
        

        
        
       

