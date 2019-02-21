<template>
  <div class="hello">
    <h1>{{ msg }}</h1>
    <input name="search">
    <button v-on:click="performSearch">Search</button>
    <div>
      <h2>Events</h2>
    </div>
    <div>
      <b-table striped hover dark small :items="events" :fields="fields">
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

    </div>
  </div>
</template>

<script>
import axios from 'axios'
import yaml from 'js-yaml'
export default {
  name: 'HelloWorld',
  data () {
    return {
      msg: 'Welcome to CoreNet',
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
      events: []
    }
  },
  created () {
    this.getEvents()
  },
  methods: {
    performSearch: function () {
      const link = 'http://127.0.0.1:5000/'
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
        })
        .catch(error => {
          console.log(error)
        })
    },
    getEvents: function () {
      setInterval(this.performSearch, 2000)
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
</style>
