$(document).ready(function() {
      
  var states = [];

  // save the states of input checkboxes
  function saveState() {
      states = [];
      $('.modal-fav-body :input').each(function() {
          states.push(this.checked)
      });
  };
  saveState();

  // load the states of input checkboxes
  function loadState() {
    $('.modal-fav-body :input').each(function(i) {
          this.checked = states[i];
    });
  };
  
  // Get the modal
  var modal = document.getElementById("myModal");

  // Get the button that opens the modal
  var btn = document.getElementById("myBtn");

  // Get the <span> element that closes the modal
  var span = document.getElementsByClassName("close-fav")[0];

  // When the user clicks the button, open the modal 
  btn.onclick = function() {
    modal.style.display = "block";
  }

  // When the user clicks on close button, close the modal
  span.onclick = function() {
    modal.style.display = "none";
    loadState();
  }

  // When the user clicks anywhere outside of the modal, close it
  window.onclick = function(event) {
    if (event.target == modal) {
      modal.style.display = "none";
      loadState();
    }
  }
  // console.log(states);

  // define submit button behaviour
  $('#favForm').submit(function(e) {
    e.preventDefault();
    var data = [];
    // var list_names = $(this).serializeArray();
    
    $('.modal-fav-body :input').each(function() {
        if (this.checked) {
            data.push(parseInt(this.id))
        }
    });
    console.log(data);
    // $.each(list_names, function(i, field) {
    //   data.push(field.value)
    // });

    saveState();
    // console.log(states);

    if (data.length < 1) {
      data = null;
      $('#fav').removeClass('fas').addClass('far');
    } else {
      $('#fav').removeClass('far').addClass('fas');
    };
   
    var server_data;
    server_data = {'data':data}
    
    // console.log(JSON.stringify(server_data));
    $.ajax({
      url: $(this).prop('action'),
      contentType: 'application/json',
      type: $(this).prop('method'),
      data: JSON.stringify(server_data),
      dataType: 'json',
      success: function(result) {
        console.log("Result:");
        console.log(result);
      }
      // cache: false,
      // processData: false,
    });
  });
});