@web_base.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        pswd1 = request.form.get('password1')
        pswd2 = request.form.get('password2')
        gender = request.form.get('gender')
        age = request.form.get('age')
        education = request.form.get('education')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists!', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters!', category='error')
        elif len(first_name) < 2:
            flash('first name must be greater than 1 characters!', category='error')
        elif pswd1 != pswd2:
            flash('Passwords don\'t match!', category='error')
        elif len(pswd1) < 6:
            flash('password must be at least 6 characters!', category='error')
        elif age == '' or gender == '' or education == '':
            flash('gender/age/education cannot by empty!', category="error")
        else:
            # add user to databse
            new_user = User(email=email,
                            first_name=first_name,
                            password=generate_password_hash(pswd1, method='sha256'),
                            age=age,
                            gender=gender,
                            education=education)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            if mode == 'u2u':
                return redirect(url_for('web_u2u.interact_u2u'))
            return redirect(url_for('web_u2m.interact'))
    return render_template('sign-up.html', user=current_user)