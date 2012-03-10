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
function subac(name, domain) {
    var controls=new Array("name","domain");
    for (control in controls){
        $("#"+controls[control]+"control").removeClass("error");
        $("#"+controls[control]+"help").html("");
    }
    $("#namehelp").html("中英文、数字皆可，不能少于2个字符，一个月只能修改一次");
    $("#domainhelp").html("可以使用英文或数字，不能少于2个字符，一个月只能修改一次");
    var mark = 1;
    if($("#name").val().length == 0) {
        $("#namecontrol").addClass("error");
        $("#namehelp").html("用户名不能为空");
        mark = 0;
    }
    if($("#domain").val().length == 0) {
        $("#domaincontrol").addClass("error");
        $("#domainhelp").html("个性域名不能为空");
        mark = 0;
    }
    if($("#name").val().length != 0 && $("#name").val() == name && $("#domain").val().length != 0 && $("#domain").val() == domain)
        mark = 0;
    if(!mark) return false;
}
