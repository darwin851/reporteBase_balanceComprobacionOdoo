/** @odoo-module **/

import { Component, useState, onWillStart, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * GenericSelector - Componente reutilizable para selección de elementos con dropdown
 * @class
 * @extends Component
 */
export class TgrSelector extends Component {
  // Template del componente
  static template = "tgr_reports_base.TgrSelector";
  // Definición de props
  static props = {
      // Props para carga desde el servidor
      modelName: { type: String, optional: true },
      domain: { type: Array, optional: true },
      fields: { type: Array, optional: true },
      limit: { type: Number, optional: true },
      
      // Props para datos directos
      items: { type: Array, optional: true },
      
      // Props para configuración de campos
      idField: { type: String, optional: true},
      displayField: { type: String, optional: true},
      secondaryField: { type: String, optional: true },
      
      // Props para estado inicial
      initialSelectedItems: { type: Array, optional: true },
      
      // Props para personalización visual
      title: { type: String, optional: true},
      icon: { type: String, optional: true},
      buttonMinWidth: { type: String, optional: true },
      
      // Props para textos
      selectAllText: { type: String, optional: true},
      deselectAllText: { type: String, optional: true},
      noItemsText: { type: String, optional: true},
      
      // Props para eventos
      onSelectionChange: { type: Function, optional: true },
  };
  static defaultProps= {
    idField:'id',
    displayField: 'name',
    title: 'Items',
    icon:'fa-list',
    buttonMinWidth:'200px',
    selectAllText:'Seleccionar Todo',
    deselectAllText:'Deseleccionar Todo',
    noItemsText:'No hay elementos disponibles'
  }

    /**
     * @override
     */
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            items: [],
            selectedItems: this.props.initialSelectedItems || [],
            isLoading: true,
        });

        onWillStart(async () => {
            if (this.props.items) {
                // Si los items se proporcionan directamente como prop
                this.state.items = this.props.items;
                this.state.isLoading = false;
            } else if (this.props.modelName) {
                // Si se debe cargar los items desde un modelo
                await this.loadItems();
            } else {
                this.state.isLoading = false;
            }
        });
        // En la función setup() de TgrSelector
        onWillUpdateProps(nextProps => {
          if (nextProps.items && JSON.stringify(nextProps.items) !== JSON.stringify(this.props.items)) {
              console.log("TgrSelector: items prop changed", nextProps.items);
              this.state.items = nextProps.items;
              this.state.isLoading = false;
          }
        });
    }

    /**
     * Carga elementos desde el servidor si se proporciona un modelName
     * @returns {Promise<void>}
     */
    async loadItems() {
        try {
            this.state.isLoading = true;
            const items = await this.orm.searchRead(
                this.props.modelName,
                this.props.domain || [],
                this.props.fields || [this.props.idField, this.props.displayField],
                { limit: this.props.limit || 0 }
            );
            this.state.items = items;
        } catch (error) {
            console.error(`Error al cargar ${this.props.title || 'elementos'}:`, error);
        } finally {
            this.state.isLoading = false;
        }
    }

    /**
     * Maneja el clic en un elemento para seleccionarlo/deseleccionarlo
     * @param {any} itemId - ID o valor único del elemento seleccionado
     */
    toggleItem(itemId) {
        const index = this.state.selectedItems.indexOf(itemId);
        if (index >= 0) {
            // Si ya está seleccionado, lo eliminamos
            const newSelected = [...this.state.selectedItems];
            newSelected.splice(index, 1);
            this.state.selectedItems = newSelected;
        } else {
            // Si no está seleccionado, lo agregamos
            this.state.selectedItems = [...this.state.selectedItems, itemId];
        }

        // Notificar al componente padre sobre el cambio
        this.props.onSelectionChange && this.props.onSelectionChange(this.state.selectedItems);
    }

    /**
     * Verifica si un elemento está seleccionado
     * @param {any} itemId - ID o valor único del elemento
     * @returns {boolean} - true si está seleccionado
     */
    isItemSelected(itemId) {
        return this.state.selectedItems.includes(itemId);
    }

    /**
     * Selecciona todos los elementos
     */
    selectAll() {
        this.state.selectedItems = this.state.items.map(item => item[this.props.idField || 'id']);
        this.props.onSelectionChange && this.props.onSelectionChange(this.state.selectedItems);
    }

    /**
     * Deselecciona todos los elementos
     */
    deselectAll() {
        this.state.selectedItems = [];
        this.props.onSelectionChange && this.props.onSelectionChange(this.state.selectedItems);
    }

    /**
     * Obtiene los nombres o etiquetas de los elementos seleccionados para mostrar
     * @returns {Array} - Array con los nombres o etiquetas de los elementos seleccionados
     */
    getSelectedItemsDisplay() {
        const idField = this.props.idField || 'id';
        const displayField = this.props.displayField || 'name';
        
        return this.state.items
            .filter(item => this.state.selectedItems.includes(item[idField]))
            .map(item => item[displayField]);
    }
}

