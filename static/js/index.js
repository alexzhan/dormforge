function submitfunction(){
    var mark = 1;
    if($("#username").val().length == 0){
        $("#idcontrol-group").removeClass();
        $("#idcontrol-group").addClass("control-group error");
        mark = 0;
    }
    if($("#password").val().length == 0) {
        $("#passwordcontrol-group").removeClass();
        $("#passwordcontrol-group").addClass("control-group error");
        mark = 0;
    }
    if(!mark) return false;
}
