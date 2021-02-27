/* from jquery import *
 * from utils import getAge
 */
function configure_titulo(data) {
    var campos = $('.fieldset_titulo_eleitor .form-group');
    if (maior_idade(data)) {
        campos.addClass('required');
        campos.find(':input').prop('required', true);
    } else {
        campos.removeClass('required');
        campos.find(':input').prop('required', false);
    }
}


jQuery(document).ready(function () {
    var nascimento = $('#id_nascimento');
    var data = nascimento.val();
    configure_titulo(data);
    nascimento.change(function () {
        var data = $(this).val();
        configure_titulo(data);
    });
});