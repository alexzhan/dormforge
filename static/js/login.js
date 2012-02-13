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
    if(!mark) return false;
}
