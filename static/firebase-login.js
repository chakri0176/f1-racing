'use strict';

import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-auth.js";

const firebaseConfig = {
    
};

window.addEventListener("load", function () {
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    updateUI(document.cookie);
    console.log("hello world load");
    
    // Signup for New User
    document.getElementById("sign-up").addEventListener('click', function () {
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();

        // Client-side validation
        if (!email || !password) {
            document.getElementById("error-message").innerText = "Email and password cannot be empty.";
            return;
        }
        if (password.length < 6) {
            document.getElementById("error-message").innerText = "Password must be at least 6 characters.";
            return;
        }

        createUserWithEmailAndPassword(auth, email, password)
            .then((userCredential) => {
                const user = userCredential.user;
                user.getIdToken().then((token) => {
                    document.cookie = "token=" + token + ";path=/;SameSite=Strict";
                    window.location = "/";
                });
            })
            .catch((error) => {
                console.log(error.code + " " + error.message);
                document.getElementById("error-message").innerText = error.message;
            });
    });

    // Login for an existing user
    document.getElementById("login").addEventListener('click', function () {
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();

        if (!email || !password) {
            document.getElementById("error-message").innerText = "Email and password cannot be empty.";
            return;
        }

        signInWithEmailAndPassword(auth, email, password)
            .then((userCredential) => {
                const user = userCredential.user;
                console.log("Logged in");
                user.getIdToken().then((token) => {
                    document.cookie = "token=" + token + ";path=/;SameSite=Strict";
                    window.location = "/";
                });
            })
            .catch((error) => {
                console.log(error.code + " " + error.message);
                document.getElementById("error-message").innerText = error.message;
            });
    });

    // Signout from firebase
    document.getElementById("sign-out").addEventListener('click', function () {
        signOut(auth)
            .then(() => {
                document.cookie = "token=;path=/;SameSite=Strict";
                window.location = "/";
            });
    });
});

function updateUI(cookie) {
    var token = parseCookieToken(cookie);
    if (token.length > 0) {
        document.getElementById("login-box").hidden = true;
        document.getElementById("sign-out").hidden = false;
    } else {
        document.getElementById("login-box").hidden = false;
        document.getElementById("sign-out").hidden = true;
    }
}

function parseCookieToken(cookie) {
    var strings = cookie.split(';');
    for (let i = 0; i < strings.length; i++) {
        var temp = strings[i].split('=');
        if (temp[0].trim() == "token")
            return temp[1];
    }
    return "";
}
