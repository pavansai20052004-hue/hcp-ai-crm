import { configureStore } from "@reduxjs/toolkit";

import crmReducer from "./crmSlice.js";

export const store = configureStore({
  reducer: {
    crm: crmReducer
  }
});

