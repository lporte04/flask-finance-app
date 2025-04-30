/* helpers */

/**
 * renumbers all input fields in a table to maintain sequential indexes (so that they can be processed by the server)
 * @param {string} tableId - html id  of the table to renumber
 * @param {string} prefix - prefix used in field names (e.g., 'expenses')
 */
function renumber(tableId, prefix){
    // get all rows in the table body and interate by index
    document.querySelectorAll(`#${tableId} tbody tr`).forEach((row, i) => {
      row.querySelectorAll('input,select').forEach(el => { // get all inputs and selects in the row, update name attributes
        // replace existing index with new index. Regex is used to match the prefix and existing index and replace it with the new index. This is necessary to ensure that the server can process the data correctly.
        el.name = el.name.replace(new RegExp(`^${prefix}-\\d+-`),
                                  `${prefix}-${i}-`);
      });
    });
  }
  
  /**
 * removes a table row and renumbers remaining rows
 * @param {HTMLElement} btn - button element that triggered the removal
 * @param {string} tableId - html id of the containing table
 * @param {string} prefix - prefix used in field names
 */
  function removeRow(btn, tableId, prefix){
    btn.closest('tr').remove();
    renumber(tableId, prefix);
  }
  
  /**
 * set up the "Add Row" button functionality for a table
 * @param {string} buttonId - html id of the add button
 * @param {string} tableId - html id of the target table
 * @param {Function} templateFn - function that returns HTML for a new row
 */
  function setupAddRow(buttonId, tableId, prefix, templateFn){
    const btn = document.getElementById(buttonId);
    if(!btn) return; // exit if button not found
  
    btn.addEventListener('click', ()=>{
      const tbody = document.querySelector(`#${tableId} tbody`); // get the table body
      const newIndex = tbody.querySelectorAll('tr').length; // calculate the index for the new row (equal to the number of existing rows)
      tbody.insertAdjacentHTML('beforeend', templateFn(newIndex)); // insert the new row at the end of the table body
    });
  }
  
  /* 
  * row templates 
  * each function returns html for a new row of the specified table type
  */
  function expenseTemplate(i){
    return `<tr>
      <td><input type="hidden" name="expenses-${i}-id">
          <input name="expenses-${i}-name" class="form-control" required></td>
      <td><input name="expenses-${i}-amount" class="form-control" type="number" step="0.01" required></td>
      <td><select name="expenses-${i}-frequency" class="form-select" required>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select></td>
      <td><button type="button" class="btn btn-sm btn-danger"
                  onclick="removeRow(this,'expenses-table','expenses')">×</button></td>
    </tr>`;
  }
  
  function goalTemplate(i){
    return `<tr>
      <td><input type="hidden" name="goals-${i}-id">
          <input name="goals-${i}-item" class="form-control" required></td>
      <td><input name="goals-${i}-cost" class="form-control" type="number" step="0.01" required></td>
      <td><button type="button" class="btn btn-sm btn-danger"
                  onclick="removeRow(this,'goals-table','goals')">×</button></td>
    </tr>`;
  }
  
  function spendingTemplate(i){
    const today = new Date().toISOString().split('T')[0];
    return `<tr>
      <td><input type="hidden" name="spendings-${i}-id">
          <input name="spendings-${i}-item" class="form-control" required></td>
      <td><input name="spendings-${i}-amount" class="form-control" type="number" step="0.01" required></td>
      <td><input name="spendings-${i}-date" class="form-control" type="date" value="${today}" required></td>
      <td><button type="button" class="btn btn-sm btn-danger"
                  onclick="removeRow(this,'spendings-table','spendings')">×</button></td>
    </tr>`;
  }
  
  function assetTemplate(i){
    return `<tr>
      <td><input type="hidden" name="assets-${i}-id">
          <input name="assets-${i}-name" class="form-control" required></td>
      <td><input name="assets-${i}-value" class="form-control" type="number" step="0.01" required></td>
      <td><button type="button" class="btn btn-sm btn-danger"
                  onclick="removeRow(this,'assets-table','assets')">×</button></td>
    </tr>`;
  }
  
  function investmentTemplate(i){
    return `<tr>
      <td><input type="hidden" name="investments-${i}-id">
          <input name="investments-${i}-stock_name" class="form-control" required></td>
      <td><input name="investments-${i}-amount" class="form-control" type="number" step="0.01" required></td>
      <td><button type="button" class="btn btn-sm btn-danger"
                  onclick="removeRow(this,'investments-table','investments')">×</button></td>
    </tr>`;
  }
  
  /* initialize on page load */
  document.addEventListener('DOMContentLoaded', () => {
    /* add-row buttons */
    setupAddRow('add-expense', 'expenses-table', 'expenses', expenseTemplate);
    setupAddRow('add-goal', 'goals-table', 'goals', goalTemplate);
    setupAddRow('add-spending', 'spendings-table', 'spendings', spendingTemplate);
    setupAddRow('add-asset', 'assets-table', 'assets', assetTemplate);
    setupAddRow('add-investment', 'investments-table', 'investments', investmentTemplate);
  
    /* renumber all tables on page load to ensure proper indexes */
    ['expenses','goals','spendings','assets','investments'].forEach(prefix =>
      renumber(`${prefix}-table`, prefix)
    );
  
    /* toggle the footer buttons when user changes tabs */
    document.querySelectorAll('button[data-bs-toggle="tab"]').forEach(tab => {
      tab.addEventListener('shown.bs.tab', e => {
        const target = e.target.getAttribute('data-bs-target');
        // show/hide buttons based on active tab
        document.getElementById('save-button').style.display = target === '#deposit' ? 'none' : 'block';
        document.getElementById('deposit-button').style.display = target === '#deposit' ? 'block' : 'none';
      });
    });
  });