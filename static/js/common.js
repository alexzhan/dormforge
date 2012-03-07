function getCookie(name) {
    var r = document.cookie.match('\\b' + name + '=([^;]*)\\b');
    return r ? r[1] : undefined;
}
function isMail(mail) {
    var filter = /^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})$/;
    if (filter.test(mail)) return true;
    else return false;
}
function isDomain(domain) {
    var filter = /^([a-zA-Z0-9_])+$/;
    if (filter.test(domain)) return true;
    else return false;
}
