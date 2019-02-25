<template>
  <div class="hello">
    <h1>{{ msg }}</h1>
    <div class="bottom-pad"></div>

    <div>
      <input name="search">
      <button v-on:click="performSearch">Search</button>
    </div>

    <div class="bottom-pad"></div>
    <div>
      <b-container fluid>
        <b-table
          striped
          hover
          dark
          small
          bordered
          show-empty
          :items="events"
          :fields="fields"
          :current-page="currentPage"
          :per-page="perPage"
        >
          <template slot="body" slot-scope="row">
            <b-button size="sm" @click="row.toggleDetails" class="mr-2">
              {{ row.detailsShowing ? 'Hide' : 'Show'}} Details
            </b-button>
          </template>
          <template slot="row-details" slot-scope="row">
            <b-card>
              <b-row class="mb-2 details">
                <b-col sm="3" class="text-sm-right"><b>Body:</b></b-col>
                <b-col>{{ row.item.body }}</b-col>
              </b-row>
              <b-button size="sm" @click="row.toggleDetails">Hide Details</b-button>
            </b-card>
          </template>
        </b-table>

        <div class="mt-3 text-center">
          <b-pagination
            :total-rows="totalRows"
            :per-page="perPage"
            v-model="currentPage"
            class="my-0"
            align="center"
          />
        </div>
      </b-container>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import yaml from 'js-yaml'
export default {
  name: 'Events',
  data () {
    return {
      msg: 'Events',
      fields: [
        {
          key: 'name',
          label: 'Name',
          sortable: true
        },
        {
          key: 'time',
          label: 'Date',
          formatter: 'convertIsoDate',
          sortable: true
        },
        {
          key: 'priority',
          label: 'Priority',
          formatter: 'toTitle',
          sortable: true
        },
        {
          key: 'type',
          label: 'Type',
          formatter: 'toUpper',
          sortable: true
        },
        {
          key: 'uuid',
          label: 'UUID',
          sortable: true
        },
        {
          key: 'body',
          label: 'Description'
        }
      ],
      totalRows: 50,
      perPage: 10,
      currentPage: 1,
      events: this.performSearch()
    }
  },
  created () {
    this.getEvents()
    // this.performSearch()
  },
  computed () {
    // sortOptions() {
    //   // Create an options list from our fields
    //   return this.fields
    //     .filter(f => f.sortable)
    //     .map(f => {
    //       return { text: f.label, value: f.key }
    //     })
    // }
  },
  methods: {
    performSearch: function () {
      const link = 'http://10.49.227.135:5000/'
      const apiLink = link + 'get_interface_status'

      axios
        .get(apiLink)
        .then(response => {
          const oldEvents = this.events
          this.events = response.data
          for (var i = 0; i < this.events.length; i++) {
            this.$set(this.events[i], '_showDetails', false)
            this.events[i].body = this.toString(this.events[i].body)
            for (var j = 0; j < oldEvents.length; j++) {
              if (this.events[i].uuid === oldEvents[j].uuid) {
                this.events[i]._showDetails = oldEvents[j]._showDetails
              }
            }
          }
          this.totalRows = this.events.length
        })
        .catch(error => {
          console.log(error)
        })
    },
    getEvents: function () {
      setInterval(this.performSearch, 1000)
    },
    convertIsoDate: function (isodate) {
      let date = new Date(isodate)
      let year = date.getFullYear()
      let month = date.getMonth() + 1
      let dt = date.getDate()
      let hour = date.getHours()
      let minutes = date.getMinutes()
      let seconds = date.getSeconds()

      if (dt < 10) {
        dt = '0' + dt
      }
      if (month < 10) {
        month = '0' + month
      }
      if (hour < 10) {
        hour = '0' + hour
      }
      if (minutes < 10) {
        minutes = '0' + minutes
      }
      if (seconds < 10) {
        seconds = '0' + seconds
      }

      let output = dt + '-' + month + '-' + year + ' ' + hour + ':' + minutes + ':' + seconds
      return output
    },
    toUpper: function (string) {
      return string.toUpperCase()
    },
    toTitle: function (string) {
      let str = string.toLowerCase()
      str = str.split(' ')

      for (var i = 0; i < str.length; i++) {
        str[i] = str[i].charAt(0).toUpperCase() + str[i].slice(1)
      }

      return str.join(' ')
    },
    toString: function (string) {
      let y = yaml.dump(JSON.parse(JSON.stringify(string)))
      return y
    },
    onFiltered: function (filteredItems) {
      // Trigger pagination to update the number of buttons/pages due to filtering
      this.totalRows = filteredItems.length
      this.currentPage = 1
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h1, h2 {
  font-weight: normal;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
.details {
  color: #000000;
}
.bottom-pad {
  margin-bottom: 10px
}
</style>
