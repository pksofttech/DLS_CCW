"use strict";
// Update 08:59

const DEBUG_MODE = true;
const HOME_ROUTE = "/home";
var token = "";
var current_content = "";
var previous_content = "";
// var page_index = 0;
//  TOKEN_EXP = 8 H.
const TOKEN_EXP = 60 * 60 * 8;

// function print(msg) {
//     console.log(msg);
// }

// function debug(msg) {
//     if (DEBUG_MODE) {
//         // console.icon("bulb","x")
//         console.log(`%cDebug: %c ${msg}`, "color:DarkBlue;", "color:DarkCyan;");
//         if (typeof msg == "object") {
//             console.log(msg);
//         }
//     }
// }

const debug = console.log;

function print_info(msg) {
    console.info(msg);
}

function print_warn(msg) {
    console.warn(msg);
}

function print_error(msg) {
    console.log(`%cError: %c ${msg}`, "color:DarkRed;", "color:DarkCyan;");
    // console.error(msg);
}

if (DEBUG_MODE) {
    print_warn("Debug Mode Enable!!!");
}

function dateTimeToStr(dateTime, format = "YYYY/MM/DD HH:mm:ss") {
    // debug(dateTime)
    return moment(dateTime).format(format);
}

var bg_mode_theme = "#aaa";
const toastMixin = Swal.mixin({
    // width: '600px',
    background: bg_mode_theme,
    toast: true,
    icon: "success",
    title: "General Title",
    animation: false,
    position: "center",
    showConfirmButton: false,
    timer: 1500,
    timerProgressBar: true,
    didOpen: (toast) => {
        toast.addEventListener("mouseenter", Swal.stopTimer);
        toast.addEventListener("mouseleave", Swal.resumeTimer);
    },
});

async function dialog_confirm({ text = "Warning, your Confirm to do.", title = "Are you sure?" } = {}) {
    try {
        const alert = await Swal.fire({
            title: title,
            text: text,
            icon: "warning",
            showCancelButton: true,
            confirmButtonColor: "#FF7E00",
            confirmButtonText: "Yes, Confirm it!",
            cancelButtonText: "No, Cancel it",
        });
        return !!(alert.value && alert.value === true);
    } catch (e) {
        console.log("error:", e);
        return false;
    }
}

function active_side_menu_bar() {
    const _class_icon_active = "text-light";
    const sb = document.getElementsByClassName("nav-sidebar")[0];
    if (sb === undefined) {
        print_warn("Page Not Side Bar");
        return;
    }
    const side_bars = sb.getElementsByClassName("nav-link");

    const url = String(window.location);
    // debug(url)
    for (let index = 0; index < side_bars.length; index++) {
        const e = side_bars[index];
        // print_info(e.href)
        if (url.indexOf(e.href) == 0) {
            e.classList.add("active");
            side_bars[index].children[0].classList.add(_class_icon_active);
            side_bars[index].children[1].classList.add(_class_icon_active);
        } else {
            // e.classList.remove('active');
        }
    }
}

let theme = getCookie("theme");
debug("UI Theme:" + theme);
theme_ui(theme);
active_side_menu_bar();
try {
    document.getElementById("nav_link_breadcrumb").innerHTML = window.location.pathname;
} catch (err) {
    print_error(err);
}

function password_keyup() {
    if (event.key === "Enter") {
        login();
    }
}

function user_keyup() {
    if (event.key === "Enter") {
        document.getElementById("user_password").focus();
    }
}

function setCookie(cname, value, expire = 0) {
    let _expires = "0";
    if (expire != 0) {
        const d = new Date();
        d.setTime(d.getTime() + expire * 1000);
        _expires = d.toGMTString();
    }

    let expires = "expires=" + _expires;
    const _cookie = cname + "=" + value + ";" + expires + ";path=/";
    document.cookie = _cookie;
    debug("Set Cookie:" + _cookie);
}

function getCookie(cname) {
    let name = cname + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(";");
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == " ") {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

async function get_headers() {
    const _token = getCookie("Authorization");
    const headers_json = {
        accept: "application/json",
        Authorization: _token,
        "Content-Type": "application/json",
    };
    return headers_json;
}

async function get_user_session() {
    const user_session = await fetchApi("/login_session", "get", null, "json");
    const ss_user = user_session.username;
    const ss_user_level = user_session.user_level;
    setCookie("ss_user", ss_user, 0);
    setCookie("ss_user_level", ss_user_level, 0);
    debug(user_session);
    // await Swal.fire(ss_user_level, ss_user, 'success')
    window.location.href = HOME_ROUTE;
}

async function checkCookie() {
    let _token = getCookie("Authorization");
    if (_token != "") {
        token = _token;
        debug("load by token Auto login by cookie");
        debug(token);

        await get_user_session();
        // window.location.href = HOME_ROUTE
    } else {
        toastMixin.fire({
            background: bg_mode_theme,
            title: "สวัดดี\nยินดีต้อนรับ",
            icon: "info",
        });
        debug("ไม่พบการลงชื่อเข้าระบบ");
    }
}

function logout() {
    Swal.fire({
        icon: "info",
        title: "Logout",
        text: "Thankyou",
        footer: "***",
    });
    Swal.fire({
        icon: "info",
        title: "Do you want to Logout system?",
        showCancelButton: true,
        confirmButtonText: "OK",
        denyButtonText: `Don't Logout`,
    }).then((result) => {
        /* Read more about isConfirmed, isDenied below */
        if (result.isConfirmed) {
            Swal.fire("Logout!", "", "success");
            document.cookie = "Authorization=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            location.reload();
        }
    });
}

async function login() {
    debug("Login");
    if (document.getElementById("user_name").value == "") {
        Swal.fire("ข้อผิดพลาด", "กรุณาป้อนชื่อผู้ใช้งานระบบ", "error").then((result) => {});
        return;
    }
    if (document.getElementById("user_password").value == "") {
        Swal.fire("ข้อผิดพลาด", "กรุณาป้อน password ผู้ใช้งานระบบ", "error").then((result) => {});
        return;
    }

    let _user = document.getElementById("user_name").value;
    let _password = document.getElementById("user_password").value;

    const params_oauth = new URLSearchParams();
    // params.append("grant_type", "password");
    params_oauth.append("username", _user);
    params_oauth.append("password", _password);
    // params.append("client_id", "jeff-client");
    // params.append("client_secret", "jeff-client");

    const response = await fetch("oauth", {
        method: "POST",
        body: params_oauth,
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
    });
    const responseData = await response.json();
    debug(responseData);
    if (responseData.access_token != null) {
        token = `${responseData.token_type} ${responseData.access_token}`;
        const remember_status = document.getElementById("remember").checked;
        console.log(remember_status);
        if (remember_status) {
            setCookie("Authorization", token, TOKEN_EXP);
        } else {
            setCookie("Authorization", token, 0);
        }
        console.log(getCookie("Authorization"));
        await get_user_session();
        // window.location.href = HOME_ROUTE
    } else {
        console.log(responseData);
        Swal.fire("ข้อผิดพลาด", String(responseData.detail), "error").then((result) => {
            return;
        });
    }
}

function set_dark_mode(v) {
    const _exp = 60 * 60 * 24 * 365;
    if (v.checked) {
        setCookie("theme", "dark", _exp);
        theme_ui("dark");
    } else {
        setCookie("theme", "light", _exp);
        theme_ui("light");
    }
}

function theme_ui(theme) {
    const _body = document.body;
    const navbar_app = document.getElementsByClassName("navbar")[0];
    const theme_check_ui = document.getElementById("theme_check_ui");
    if ((navbar_app == undefined) | (theme_check_ui == undefined)) {
        return;
    }
    switch (theme) {
        case "dark":
            _body.classList.add("dark-mode");
            // navbar_app.classList.remove('navbar-white navbar-light');
            navbar_app.classList.remove("navbar-light");
            navbar_app.classList.add("navbar-dark");
            bg_mode_theme = "#555";
            theme_check_ui.checked = true;
            break;
        case "light":
            _body.classList.remove("dark-mode");
            navbar_app.classList.remove("navbar-dark");
            navbar_app.classList.add("navbar-light");
            bg_mode_theme = "#fff";
            theme_check_ui.checked = false;
            break;

        default:
            break;
    }
}

function goto_route(path = "") {
    debug("Goto path:" + path);
    if (path == "") {
        window.location.href = HOME_ROUTE;
    } else {
        window.location.href = path;
    }
}

async function fetchApi(path = "", method = "get", body = null, returnType = "text", echo = true) {
    // debug(String(typeof (body)))
    const _token = getCookie("Authorization");
    const headers_json = {
        accept: "application/json",
        Authorization: _token,
        "Content-Type": "application/json",
    };
    const headers_form = {
        accept: "application/json",
        Authorization: _token,
        // 'Content-Type': 'multipart/form-data',
    };
    let headers = headers_json;
    if (typeof body == "object") {
        // debug("multipart/form-data")
        headers = headers_form;
    }
    // debug(`Fetch : ${path} => ${method}\nBody: ${body}\nAuthorization : ${_token}`)
    if ((returnType != "text") & echo) {
        Swal.fire({
            icon: "success",
            html: "<h5>waiting...</h5>",

            showCancelButton: false,
            showConfirmButton: false,
        });
    }
    let response = null;
    try {
        response = await fetch(path, {
            method: method,
            headers: headers,
            body: body,
        });
    } catch (err) {
        print_error(err);
    } finally {
        swal.close();
    }

    switch (response.status) {
        case 401:
            debug(response.status);
            document.cookie = "Authorization=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            Swal.fire("session expires", "กรุณาลงชื่อเข้าใช้งานระบบ", "error").then((result) => {
                location.reload();
            });

            break;
        case 200:
            if (returnType === "text") {
                let _t = await response.text();
                return _t;
            }
            if (returnType === "json") {
                let data = await response.json();
                return data;
            }
            break;
        default:
            // debug(response)
            const msg_resp = await response.text();
            toastMixin.fire({
                background: bg_mode_theme,
                title: `${response.status}`,
                text: `${response.statusText}\n${msg_resp}`,
                icon: "error",
            });
            break;
    }
    // return responseData;
}
