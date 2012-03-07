function subch(){
    var controls=new Array("old","new","confirm");
    for (control in controls){
        $("#"+controls[control]+"control").removeClass("error");
        $("#"+controls[control]+"help").html("");
    }
    var mark = 1;
    if($("#old").val().length == 0) {
        $("#oldcontrol").addClass("error");
        $("#oldhelp").html("请输入当前密码");
        mark = 0;
    }
    if($("#new").val().length == 0) {
        $("#newcontrol").addClass("error");
        $("#newhelp").html("请输入新密码");
        mark = 0;
    }
    if($("#confirm").val().length == 0) {
        $("#confirmcontrol").addClass("error");
        $("#confirmhelp").html("请输入新密码确认");
        mark = 0;
    }
    if($("#new").val().length > 32) {
        $("#newcontrol").addClass("error");
        $("#newhelp").html("密码长度不能超过 32 个字符");
        mark = 0;
    }
    if($("#confirm").val().length != 0 && $("#new").val() != $("#confirm").val()) {
        $("#confirmcontrol").addClass("error");
        $("#confirmhelp").html("两次密码输入不一致");
        mark = 0;
    }
    if(!mark) return false;
}
