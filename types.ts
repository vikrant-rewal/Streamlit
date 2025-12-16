export interface MealPlanResponse {
  menuText: string;
}

export enum MealType {
  Breakfast = 'Breakfast',
  Lunch = 'Lunch',
  Dinner = 'Dinner',
}

export interface SettingsState {
  isWeekend: boolean;
}
