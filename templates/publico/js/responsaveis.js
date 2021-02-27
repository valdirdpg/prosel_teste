/* from jquery import *
 * from utils import exists, getAge
 */
function configure_responsaveis(data) {
    var nome = $('#id_nome_responsavel');
    var parentesco = $('#id_parentesco_responsavel');
    var email = $('#id_email_responsavel');
    var row_nome = nome.closest('.form-group');
    var row_parentesco = parentesco.closest('.form-group');
    if(email.exists()) {
        var row_email = email.closest('.form-group');
    }
    if (maior_idade(data)) {
        row_nome.slideUp(150);
        row_nome.removeClass('required');
        nome.prop('required', false);
        row_parentesco.slideUp(150);
        row_parentesco.removeClass('required');
        parentesco.prop('required', false);
        if(email.exists()) {
            row_email.slideUp(150);
        }
    } else {
        row_nome.slideDown(150);
        row_nome.addClass('required');
        nome.prop('required', true);
        row_parentesco.slideDown(150);
        row_parentesco.addClass('required');
        parentesco.prop('required', true);
        if(email.exists()) {
            row_email.slideDown(150);
        }
    }
}

function clean_responsaveis() {
    $('#id_nome_responsavel').val('');
    if($('#id_email_responsavel').exists()) {
        $('#id_email_responsavel').val('');
    }
    $('#id_parentesco_responsavel option:selected').removeAttr('selected');
}


jQuery(document).ready(function () {
    var nascimento = $('#id_nascimento');
    var data = nascimento.val();
    configure_responsaveis(data);
    nascimento.change(function () {
        var new_data = $(this).val();
        configure_responsaveis(new_data);
        if (maior_idade(data) && !maior_idade(new_data)) {
            clean_responsaveis();
        }
    });
});