from flask import Flask, render_template, redirect, url_for, request, flash, session
from web3 import Web3
from web3.middleware import geth_poa_middleware
from contract_info import abi, contract_address  
import re

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './tmp'
app.config['SESSION_FILE_THRESHOLD'] = 500


W3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
W3.middleware_onion.inject(geth_poa_middleware, layer=0)
contract = W3.eth.contract(address=contract_address, abi=abi)

def validate_password(password):
    if len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов."
    if not re.search("[0-9]", password):
        return False, "Пароль должен содержать хотя бы одну цифру."
    if not re.search("[A-Z]", password):
        return False, "Пароль должен содержать хотя бы одну заглавную букву."
    if not re.search("[a-z]", password):
        return False, "Пароль должен содержать хотя бы одну строчную букву."
    if not re.search("[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Пароль должен содержать хотя бы один специальный символ."
    return True, "Пароль валиден."

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        password = request.form.get('password')
        is_valid, error_message = validate_password(password)
        if is_valid:
            try:
                address = W3.geth.personal.new_account(password)
                flash(f'Аккаунт успешно создан: {address}', 'success')
                session['new_account_address'] = address  
                return redirect(url_for('register_success'))  
            except Exception as e:
                
                if hasattr(e, 'args') and len(e.args) > 0 and 'revert' in e.args[0]:
                    revert_message = e.args[0].split('revert ')[1]
                    flash(f'Ошибка регистрации: {revert_message}', 'error')
                else:
                    flash(f'Ошибка регистрации: {e}', 'error')
                return render_template("register.html")
        else:
            flash(f'Ошибка: {error_message}', 'error')
            return render_template("register.html")
    else:
        return render_template("register.html")


@app.route('/register_success')
def register_success():
    address = session.get('new_account_address')
    if address:
        return render_template("register_success.html", address=address)
    else:
        flash("Ошибка! Не удалось найти адрес нового аккаунта.", 'error')
        return redirect(url_for('index')) 



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        public_key = request.form.get('public_key')
        password = request.form.get('password')
        try:
            W3.geth.personal.unlock_account(public_key, password)
            flash('Авторизация успешна', 'success')
            return redirect(url_for('dashboard', public_key=public_key))
        except Exception as e:
            flash(f'Ошибка авторизации: {e}', 'error')
            return render_template("login.html")
    else:
        return render_template("login.html")



@app.route('/dashboard/<public_key>')
def dashboard(public_key):
    balance = W3.eth.get_balance(public_key)
    return render_template('dashboard.html', public_key=public_key, balance=balance)


@app.route('/withdraw/<public_key>', methods=['POST'])
def withdraw(public_key):
    to = request.form.get('to')
    amount = int(request.form.get('amount'))
    try:
        tx_hash = contract.functions.withdrawll(to, amount).transact({
            'from': public_key,
        })
        flash(f'Транзакция успешно отправлена: {tx_hash.hex()}', 'success')
        return redirect(url_for('dashboard', public_key=public_key))
    except Exception as e:
      
        if hasattr(e, 'args') and len(e.args) > 0 and 'revert' in e.args[0]:
            revert_message = e.args[0].split('revert ')[1]
            flash(f'Ошибка: {revert_message}', 'error')
        else:
            flash(f'Ошибка: {e}', 'error')
        return redirect(url_for('dashboard', public_key=public_key))

@app.route('/update_estate_status/<public_key>', methods=['POST'])
def update_estate_status(public_key):
    estate_id = int(request.form.get('estate_id'))
    new_status = bool(request.form.get('new_status'))
    try:
        tx_hash = contract.functions.updateEstateStatus(estate_id, new_status).transact({
            'from': public_key
        })
        flash(f'Статус недвижимости обновлен: {tx_hash.hex()}', 'success')
        return redirect(url_for('dashboard', public_key=public_key))
    except Exception as e:
       
        if hasattr(e, 'args') and len(e.args) > 0 and 'revert' in e.args[0]:
            revert_message = e.args[0].split('revert ')[1]
            flash(f'Ошибка: {revert_message}', 'error')
        else:
            flash(f'Ошибка: {e}', 'error')
        return redirect(url_for('dashboard', public_key=public_key))


@app.route('/create_ad/<public_key>', methods=['POST'])
def create_ad(public_key):
    estate_id = int(request.form.get('estate_id'))
    price = int(request.form.get('price'))
    try:
        tx_hash = contract.functions.createAd(estate_id, price).transact({
            'from': public_key
        })
        flash(f'Объявление успешно создано: {tx_hash.hex()}', 'success')
        return redirect(url_for('dashboard', public_key=public_key))
    except Exception as e:
       
        if hasattr(e, 'args') and len(e.args) > 0 and 'revert' in e.args[0]:
            revert_message = e.args[0].split('revert ')[1]
            flash(f'Ошибка: {revert_message}', 'error')
        else:
            flash(f'Ошибка: {e}', 'error')
        return redirect(url_for('dashboard', public_key=public_key))


@app.route('/update_ad_status/<public_key>', methods=['POST'])
def update_ad_status(public_key):
    ad_id = int(request.form.get('ad_id'))
    new_status = int(request.form.get('new_status'))
    try:
        tx_hash = contract.functions.updateAdStatus(ad_id, new_status).transact({
            'from': public_key
        })
        flash(f'Статус объявления обновлен: {tx_hash.hex()}', 'success')
        return redirect(url_for('dashboard', public_key=public_key))
    except Exception as e:
     
        if hasattr(e, 'args') and len(e.args) > 0 and 'revert' in e.args[0]:
            revert_message = e.args[0].split('revert ')[1]
            flash(f'Ошибка: {revert_message}', 'error')
        else:
            flash(f'Ошибка: {e}', 'error')
        return redirect(url_for('dashboard', public_key=public_key))


@app.route('/buy_estate/<public_key>', methods=['POST'])
def buy_estate(public_key):
    ad_id = int(request.form.get('ad_id'))
    value = int(request.form.get('value'))
    try:
        tx_hash = contract.functions.buyEstate(ad_id).transact({
            'from': public_key,
            'value': value
        })
        flash(f'Недвижимость куплена: {tx_hash.hex()}', 'success')
        return redirect(url_for('dashboard', public_key=public_key))
    except Exception as e:
        
        if hasattr(e, 'args') and len(e.args) > 0 and 'revert' in e.args[0]:
            revert_message = e.args[0].split('revert ')[1]
            flash(f'Ошибка: {revert_message}', 'error')
        else:
            flash(f'Ошибка: {e}', 'error')
        return redirect(url_for('dashboard', public_key=public_key))


@app.route('/get_estates/<public_key>')
def get_estates(public_key):
    estates = contract.functions.getEstates().call({
        'from': public_key
    })
    return render_template('estates.html', estates=estates)


@app.route('/get_ads/<public_key>')
def get_ads(public_key):
    ads = contract.functions.getAds().call({
        'from': public_key
    })
    return render_template('ads.html', ads=ads)



@app.route('/create_estate/<public_key>', methods=['POST'])
def create_estate(public_key):
    square = int(request.form.get('square'))
    rooms = int(request.form.get('rooms'))
    es_type = int(request.form.get('es_type'))
    try:
        tx_hash = contract.functions.createEstate(square, rooms, es_type).transact({
            'from': public_key
        })
        flash(f'Недвижимость успешно создана: {tx_hash.hex()}', 'success')
        return redirect(url_for('dashboard', public_key=public_key))
    except Exception as e:
        
        if hasattr(e, 'args') and len(e.args) > 0 and 'revert' in e.args[0]:
            revert_message = e.args[0].split('revert ')[1]
            flash(f'Ошибка: {revert_message}', 'error')
        else:
            flash(f'Ошибка: {e}', 'error')
        return redirect(url_for('dashboard', public_key=public_key))

if __name__ == '__main__':
    app.run(debug=True)