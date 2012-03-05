function changefunction(){
    var coltype = ['bk','ss','bs','zx'];
    for(var i = 0 ; i < coltype.length ; i++) {
        if($("#coltype").val() == coltype[i]) $('#'+coltype[i]).show();
        else $('#'+coltype[i]).hide();
    }
}
function submitfunction(){
    var mark = 1;
    if($("#username").val().length == 0){
        $("#idcontrol-group").removeClass();
        $("#idcontrol-group").addClass("control-group error");
        $("#usernamehelp").html("请输入用户名");
        mark = 0;
    }
    if($("#username").val().length > 16){
        $("#idcontrol-group").removeClass();
        $("#idcontrol-group").addClass("control-group error");
        $("#usernamehelp").html("用户名不能超过16个字符");
        mark = 0;
    }
    if($("#username").val().length != 0 && $("#username").val().length < 2){
        $("#idcontrol-group").removeClass();
        $("#idcontrol-group").addClass("control-group error");
        $("#usernamehelp").html("用户名不能少于2个字符");
        mark = 0;
    }
    if($("#email").val().length == 0) {
        $("#emailcontrol-group").removeClass();
        $("#emailcontrol-group").addClass("control-group error");
        $("#emailhelp").html("请输入你的邮箱");
        mark = 0;
    }
    if($("#email").val().length > 32) {
        $("#emailcontrol-group").removeClass();
        $("#emailcontrol-group").addClass("control-group error");
        $("#emailhelp").html("邮箱长度不能超过32个字符");
        mark = 0;
    }
    if($("#email").val().length != 0 && !isMail($("#email").val())) {
        $("#emailcontrol-group").removeClass();
        $("#emailcontrol-group").addClass("control-group error");
        $("#emailhelp").html("你输入的邮箱不符合规则");
        mark = 0;
    }
    if($("#password").val().length == 0) {
        $("#passwordcontrol-group").removeClass();
        $("#passwordcontrol-group").addClass("control-group error");
        $("#passwordhelp").html("请输入密码");
        mark = 0;
    }
    if($("#password").val().length > 32) {
        $("#passwordcontrol-group").removeClass();
        $("#passwordcontrol-group").addClass("control-group error");
        $("#passwordhelp").html("密码长度不能超过 32 个字符");
        mark = 0;
    }
    if($("#password_again").val().length == 0) {
        $("#passwdcontrol-group").removeClass();
        $("#passwdcontrol-group").addClass("control-group error");
        $("#passwdhelp").html("请输入确认密码");
        mark = 0;
    }
    if($("#password").val() != $("#password_again").val()) {
        $("#passwdcontrol-group").removeClass();
        $("#passwdcontrol-group").addClass("control-group error");
        $("#passwdhelp").html("两次输入的密码不一致");
        mark = 0;
    }
    if($("#coltype").val() == 'bk'){
        if($("#bkbkcollege").val().length == 0) {
            $("#bkbkcollegecontrol-group").removeClass();
            $("#bkbkcollegecontrol-group").addClass("control-group error");
            $("#bkbkcollegehelp").html("请输入学校全称");
            mark = 0;
        }
        if($("#bkbkmajor").val().length == 0) {
            $("#bkbkmajorcontrol-group").removeClass();
            $("#bkbkmajorcontrol-group").addClass("control-group error");
            $("#bkbkmajorhelp").html("请输入专业全称");
            mark = 0;
        }
        if($("#bkbkmajor").val().length != 0 && $("#bkbkmajor").val().length < 2) {
            $("#bkbkmajorcontrol-group").removeClass();
            $("#bkbkmajorcontrol-group").addClass("control-group error");
            $("#bkbkmajorhelp").html("请输入正确的专业全称");
            mark = 0;
        }
    }
    if($("#coltype").val() == 'ss'){
        if($("#sssscollege").val().length == 0) {
            $("#sssscollegecontrol-group").removeClass();
            $("#sssscollegecontrol-group").addClass("control-group error");
            $("#sssscollegehelp").html("请输入硕士学校全称");
            mark = 0;
        }
        if($("#ssssmajor").val().length == 0) {
            $("#ssssmajorcontrol-group").removeClass();
            $("#ssssmajorcontrol-group").addClass("control-group error");
            $("#ssssmajorhelp").html("请输入硕士专业全称");
            mark = 0;
        }
        if($("#ssssmajor").val().length != 0 && $("#ssssmajor").val().length < 2) {
            $("#ssssmajorcontrol-group").removeClass();
            $("#ssssmajorcontrol-group").addClass("control-group error");
            $("#ssssmajorhelp").html("请输入正确的硕士专业全称");
            mark = 0;
        }
        if($("#ssbkcollege").val().length == 0) {
            $("#ssbkcollegecontrol-group").removeClass();
            $("#ssbkcollegecontrol-group").addClass("control-group error");
            $("#ssbkcollegehelp").html("请输入本科学校全称");
            mark = 0;
        }
        if($("#ssbkmajor").val().length == 0) {
            $("#ssbkmajorcontrol-group").removeClass();
            $("#ssbkmajorcontrol-group").addClass("control-group error");
            $("#ssbkmajorhelp").html("请输入本科专业全称");
            mark = 0;
        }
        if($("#ssbkmajor").val().length != 0 && $("#ssbkmajor").val().length < 2) {
            $("#ssbkmajorcontrol-group").removeClass();
            $("#ssbkmajorcontrol-group").addClass("control-group error");
            $("#ssbkmajorhelp").html("请输入正确的本科专业全称");
            mark = 0;
        }
    }
    if($("#coltype").val() == 'bs') {
        if($("#bsbscollege").val().length == 0) {
            $("#bsbscollegecontrol-group").removeClass();
            $("#bsbscollegecontrol-group").addClass("control-group error");
            $("#bsbscollegehelp").html("请输入博士学校全称");
            mark = 0;
        }
        if($("#bsbsmajor").val().length == 0) {
            $("#bsbsmajorcontrol-group").removeClass();
            $("#bsbsmajorcontrol-group").addClass("control-group error");
            $("#bsbsmajorhelp").html("请输入博士专业全称");
            mark = 0;
        }
        if($("#bsbsmajor").val().length != 0 && $("#bsbsmajor").val().length < 2) {
            $("#bsbsmajorcontrol-group").removeClass();
            $("#bsbsmajorcontrol-group").addClass("control-group error");
            $("#bsbsmajorhelp").html("请输入正确的博士专业全称");
            mark = 0;
        }
        if($("#bssscollege").val().length == 0) {
            $("#bssscollegecontrol-group").removeClass();
            $("#bssscollegecontrol-group").addClass("control-group error");
            $("#bssscollegehelp").html("请输入硕士学校全称");
            mark = 0;
        }
        if($("#bsssmajor").val().length == 0) {
            $("#bsssmajorcontrol-group").removeClass();
            $("#bsssmajorcontrol-group").addClass("control-group error");
            $("#bsssmajorhelp").html("请输入硕士专业全称");
            mark = 0;
        }
        if($("#bsssmajor").val().length != 0 && $("#bsssmajor").val().length < 2) {
            $("#bsssmajorcontrol-group").removeClass();
            $("#bsssmajorcontrol-group").addClass("control-group error");
            $("#bsssmajorhelp").html("请输入正确的硕士专业全称");
            mark = 0;
        }
        if($("#bsbkcollege").val().length == 0) {
            $("#bsbkcollegecontrol-group").removeClass();
            $("#bsbkcollegecontrol-group").addClass("control-group error");
            $("#bsbkcollegehelp").html("请输入本科学校全称");
            mark = 0;
        }
        if($("#bsbkmajor").val().length == 0) {
            $("#bsbkmajorcontrol-group").removeClass();
            $("#bsbkmajorcontrol-group").addClass("control-group error");
            $("#bsbkmajorhelp").html("请输入本科专业全称");
            mark = 0;
        }
        if($("#bsbkmajor").val().length != 0 && $("#bsbkmajor").val().length < 2) {
            $("#bsbkmajorcontrol-group").removeClass();
            $("#bsbkmajorcontrol-group").addClass("control-group error");
            $("#bsbkmajorhelp").html("请输入正确的本科专业全称");
            mark = 0;
        }
    }
    if($("#coltype").val() == 'zx') {
        if($("#zxschool").val().length == 0) {
            $("#zxschoolcontrol-group").removeClass();
            $("#zxschoolcontrol-group").addClass("control-group error");
            $("#zxschoolhelp").html("请输入学校全称");
            mark = 0;
        }
        if($("#zxprovince").val().length == 0) {
            $("#zxprovincecontrol-group").removeClass();
            $("#zxprovincecontrol-group").addClass("control-group error");
            $("#zxprovincehelp").html("请输入省份");
            mark = 0;
        }
        if($("#zxcity").val().length == 0) {
            $("#zxcitycontrol-group").removeClass();
            $("#zxcitycontrol-group").addClass("control-group error");
            $("#zxcityhelp").html("请输入城市");
            mark = 0;
        }
    }
    if($("#domain").val().length == 0) {
        $("#domaincontrol-group").removeClass();
        $("#domaincontrol-group").addClass("control-group error");
        $("#domainhelp").html("请输入个性域名");
        mark = 0;
    }
    if($("#domain").val().length > 16) {
        $("#domaincontrol-group").removeClass();
        $("#domaincontrol-group").addClass("control-group error");
        $("#domainhelp").html("个性域名不能超过16个字符");
        mark = 0;
    }
    if($("#domain").val().length != 0 && $("#domain").val().length < 2) {
        $("#domaincontrol-group").removeClass();
        $("#domaincontrol-group").addClass("control-group error");
        $("#domainhelp").html("个性域名不能少于2个字符");
        mark = 0;
    }
    if(!isDomain($("#domain").val())) {
        $("#domaincontrol-group").removeClass();
        $("#domaincontrol-group").addClass("control-group error");
        $("#domainhelp").html("个性域名不符合规则，请使用a-zA-Z0-9_");
        mark = 0;
    }
    if(!mark) return false;
}
function usernameinfo(){
    $("#idcontrol-group").removeClass();
    $("#idcontrol-group").addClass("control-group");
    $("#usernamehelp").html("");
    if($("#username").val().length == 0){
        return false;
    }
    if($("#username").val().length > 16){
        $("#idcontrol-group").removeClass();
        $("#idcontrol-group").addClass("control-group error");
        $("#usernamehelp").html("用户名不能超过16个字符");
        return false;
    }
    if($("#username").val().length < 2){
        $("#idcontrol-group").removeClass();
        $("#idcontrol-group").addClass("control-group error");
        $("#usernamehelp").html("用户名不能少于2个字符");
        return false;
    }
    $.ajax({
        type:"POST",
        url:"/isexist",
        data:{property:$("#username").val(),propertype:"username",_xsrf:getCookie("_xsrf")},
        success:function(data){
            if(data == '已被占用'){ 
                $("#idcontrol-group").removeClass();
                $("#idcontrol-group").addClass("control-group error");
            }
            else {
                $("#idcontrol-group").removeClass();
                $("#idcontrol-group").addClass("control-group success");
            }
    $("#usernamehelp").html(decodeURI(data));
        },
        error:function(data){
                  $("#idcontrol-group").removeClass();
                  $("#idcontrol-group").addClass("control-group error");
                  $("#usernamehelp").html("Something went wrong...");
              }

    });
}
function emailinfo(){
    $("#emailcontrol-group").removeClass();
    $("#emailcontrol-group").addClass("control-group");
    $("#emailhelp").html("");
    if($("#email").val().length == 0) {
        return false;
    }
    if($("#email").val().length > 32) {
        $("#emailcontrol-group").removeClass();
        $("#emailcontrol-group").addClass("control-group error");
        $("#emailhelp").html("邮箱长度不能超过32个字符");
        return false;
    }
    if($("#email").val().length != 0 && !isMail($("#email").val())) {
        $("#emailcontrol-group").removeClass();
        $("#emailcontrol-group").addClass("control-group error");
        $("#emailhelp").html("你输入的邮箱不符合规则");
        return false;
    }
    $.ajax({
        type:"POST",
        url:"/isexist",
        data:{property:$("#email").val(),propertype:"email",_xsrf:getCookie("_xsrf")},
        success:function(data){
            if(data != '可以使用'){ 
                $("#emailcontrol-group").removeClass();
                $("#emailcontrol-group").addClass("control-group error");
            }
            else {
                $("#emailcontrol-group").removeClass();
                $("#emailcontrol-group").addClass("control-group success");
            }
    $("#emailhelp").html(decodeURI(data));
        },
        error:function(data){
                  $("#emailcontrol-group").removeClass();
                  $("#emailcontrol-group").addClass("control-group error");
                  $("#emailhelp").html("Something went wrong...");
              }

    });
}
function domaininfo(){
    $("#domaincontrol-group").removeClass();
    $("#domaincontrol-group").addClass("control-group");
    $("#domainhelp").html("");
    if($("#domain").val().length == 0) {
        return false;
    }
    if($("#domain").val().length > 16) {
        $("#domaincontrol-group").removeClass();
        $("#domaincontrol-group").addClass("control-group error");
        $("#domainhelp").html("个性域名不能超过16个字符");
        return false;
    }
    if($("#domain").val().length < 2) {
        $("#domaincontrol-group").removeClass();
        $("#domaincontrol-group").addClass("control-group error");
        $("#domainhelp").html("个性域名不能少于2个字符");
        return false;
    }
    if(!isDomain($("#domain").val())) {
        $("#domaincontrol-group").removeClass();
        $("#domaincontrol-group").addClass("control-group error");
        $("#domainhelp").html("个性域名不符合规则，请使用a-zA-Z0-9_");
        return false;
    }
    $.ajax({
        type:"POST",
        url:"/isexist",
        data:{property:$("#domain").val(),propertype:"domain",_xsrf:getCookie("_xsrf")},
        success:function(data){
            if(data != '可以使用'){ 
                $("#domaincontrol-group").removeClass();
                $("#domaincontrol-group").addClass("control-group error");
            }
            else {
                $("#domaincontrol-group").removeClass();
                $("#domaincontrol-group").addClass("control-group success");
            }
    $("#domainhelp").html(decodeURI(data));
        },
        error:function(data){
                  $("#domaincontrol-group").removeClass();
                  $("#domaincontrol-group").addClass("control-group error");
                  $("#domainhelp").html("Something went wrong...");
              }

    });
}
function passwordinfo(){
    $("#passwordcontrol-group").removeClass();
    $("#passwordcontrol-group").addClass("control-group");
    $("#passwordhelp").html("");
    if($("#password").val().length == 0) {
        return false;
    }
    if($("#password").val().length > 32) {
        $("#passwordcontrol-group").removeClass();
        $("#passwordcontrol-group").addClass("control-group error");
        $("#passwordhelp").html("密码长度不能超过 32 个字符");
        return false;
    }
}
function passwdinfo(){
    $("#passwdcontrol-group").removeClass();
    $("#passwdcontrol-group").addClass("control-group");
    $("#passwdhelp").html("");
    if($("#password_again").val().length == 0) {
        return false;
    }
    if($("#password").val() != $("#password_again").val()) {
        $("#passwdcontrol-group").removeClass();
        $("#passwdcontrol-group").addClass("control-group error");
        $("#passwdhelp").html("两次输入的密码不一致");
        return false;
    }
}
function collegeinfo(collegetype){
    collegeid = "#"+collegetype;
    collegeclass = collegeid + "control-group";
    collegehelp = collegeid + "help";
    $(collegeclass).removeClass();
    $(collegeclass).addClass("control-group");
    $(collegehelp).html("");
    if($(collegeid).val().length == 0){
        return false;
    }
    $.ajax({
        type:"POST",
        url:"/isexist",
        data:{property:$(collegeid).val(),propertype:"college",_xsrf:getCookie("_xsrf")},
        success:function(data){
            if(data != '可以注册'){ 
                $(collegeclass).removeClass();
                $(collegeclass).addClass("control-group error");
            }
            else {
                $(collegeclass).removeClass();
                $(collegeclass).addClass("control-group success");
            }
    $(collegehelp).html(decodeURI(data));
        },
        error:function(data){
                  $(collegeclass).removeClass();
                  $(collegeclass).addClass("control-group error");
                  $(collegehelp).html("Something went wrong...");
              }

    });
}
function clearinfo(clearid) {
    fullclearid = "#"+clearid;
    fullclearclass = fullclearid + "control-group";
    fullclearhelp = fullclearid + "help";
    $(fullclearclass).removeClass();
    $(fullclearclass).addClass("control-group");
    $(fullclearhelp).html("");
}
