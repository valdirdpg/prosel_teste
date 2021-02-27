$.fn.exists = function () {
    return this.length !== 0;
}


function toDate(dateStr) {
    if (dateStr === '')
        return undefined;
    var data;
    var hora;
    if (dateStr.indexOf(" ") >= 0) {
        dateStr = dateStr.split(" ");
        data = dateStr[0].split("/");
        hora = dateStr[1].split(":");
    } else {
        data = dateStr.split("/");
        hora = [0, 0]
    }
    return new Date(data[2], data[1] - 1, data[0], hora[0], hora[1]);
}


function getAge(dateString) {
    var today = new Date();
    var birthDate = toDate(dateString);
    var age = today.getFullYear() - birthDate.getFullYear();
    var m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    return age;
}


MAIORIDADE = 18; /* Anos */


function maior_idade(dateString) {
    return getAge(dateString) >= MAIORIDADE;
}