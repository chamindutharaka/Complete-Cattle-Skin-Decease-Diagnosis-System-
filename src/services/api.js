import axios from "axios";

export const diagnosisAPI = axios.create({
  baseURL: "http://localhost:5000"
});

export const monitoringAPI = axios.create({
  baseURL: "http://localhost:5001"
});