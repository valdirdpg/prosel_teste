$(document).ready(function(){

    $("input[id$='_nao_se_aplica']").each(function(){
        var id_nao_se_aplica = new String(this.id);
        var id_item = id_nao_se_aplica.substring(0, id_nao_se_aplica.indexOf("_nao_se_aplica"));
        if ($("#" + id_item).val() == ''){
            $("#" + this.id).prop('checked', true);
            $("#" + id_item).prop('disabled', true)
        }
    });

    $("input[id$='_nao_se_aplica']").change(function(){
        var id_nao_se_aplica = new String(this.id);
        var id_item = id_nao_se_aplica.substring(0, id_nao_se_aplica.indexOf("_nao_se_aplica"));
        if ($("#" + id_nao_se_aplica).is(':checked')){
            $("#" + id_item).prop('disabled', true);
            $("#" + id_item).val("");
        } else{
            $("#" + id_item).prop('disabled', false);
        }
    });
});
