
// CONTRASTE

jQuery(document).ready(function () {
    $('#alto-contraste').click(function (){
        $('body').toggleClass("contraste");
        return false;
    });
});


// ACESSIBILIDADE

function scrollToId(id){
    $('html, body').animate({
        scrollTop: $(id).offset().top
    }, 500);
}

jQuery(document).ready(function ($) {
    $(document).keyup(function(e) {
        var key = e.which - 48;
        if (key == 1 || key == 2 || key == 3 || key == 4) {
            var id = $('[data-key-bind='+key+']').attr('href');
            if (key == 3) {
                $(id).focus();
            }
            e.preventDefault();
            scrollToId(id);
        }
        return false;
    });

    $('.accessibility a').each(function() {
        $(this).click(function(){
            var id = $(this).attr('href');
            scrollToId(id);
            return false;
        });
    });
});

jQuery(function($){
    $('.disablecopypaste').on('cut copy paste focus', ':input', function (e) {
        $(this).attr( 'autocomplete', 'off' );
        e.preventDefault();
    });

});

jQuery(function($){

    // lista de máscaras
    var MASK_CPF = '999.999.999-99';
    var MASK_TITULO_ELEITOR = '9999 9999 9999';
    var MASK_DATA = '99/99/9999';
    var MASK_CEP = '99.999-999';
    var MASK_NOTA = '99.99';

    // Configuração para máscaras de telefone com 4 ou 5 dígitos.
    var maskBehaviorFone = function (val) {
      return val.replace(/\D/g, '').length === 11 ? '(00) 00000-0000' : '(00) 0000-00009';
    },
    options_fone = {onKeyPress: function(val, e, field, options) {
            field.mask(maskBehaviorFone.apply({}, arguments), options);
        }
    };

    // Os seletores devem ser separados por vírgula (,)
    $('input.mask-cpf, .mask-cpf > input').mask(MASK_CPF);
    $('input.mask-numero_titulo_eleitor, .mask-numero_titulo_eleitor > input').mask(MASK_TITULO_ELEITOR);
    $('input.mask-data, .mask-data > input, .vDateField').mask(MASK_DATA, {placeholder: "__/__/____"});
    $("input.mask-telefone, .mask-telefone > input").mask(maskBehaviorFone, options_fone);
    $("input.mask-cep, .mask-cep > input").mask(MASK_CEP);
    $("input.mask-nota, .mask-nota > input").mask(MASK_NOTA);

    // Configura classe do bootstrap CSS para campos com erro de validação.
    $( "div.error" ).each(function() {
        $(this).removeClass("error");
        $(this).addClass("has-error has-feedback");
    });

    $('[data-toggle=popover]').popover({
        container: 'body',
        html: true,
        content: function () {
            return $(this).next('.popper-content').html();
        }
    });

    $('[data-toggle=tooltip]').tooltip();
});